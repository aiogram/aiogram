//! The Python -> Rust interface of the converter core (F-08 plan-10, decision 10).
//!
//! The resolver in `aiogram/utils/_converters.py` builds [`Kind`] and [`Field`] objects through the
//! typed constructors below (`aiogram/_core.pyi`). Rust never reads attributes of the resolver's
//! objects by name: a mismatch is a mypy / stubtest error, or a `TypeError` at class creation.
//!
//! Kinds are immutable once built, except two set-once references ([`Slot`]): a model's core
//! (its fields are set later, so classes may refer to themselves or to classes defined later) and
//! a [`KindCell`] (recursive `type X = ...` aliases). Those are the only edges that may close a
//! reference cycle, so they are the ones `__clear__` drops.

use std::cell::UnsafeCell;
use std::sync::atomic::{AtomicU8, Ordering};

use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PyString, PyTuple, PyType};
use pyo3::{PyTraverseError, PyVisit};

use super::model::ModelCore;

// ---------------------------------------------------------------------------------------------
// Slot: a set-once reference that the garbage collector can clear
// ---------------------------------------------------------------------------------------------

const EMPTY: u8 = 0;
const WRITING: u8 = 1;
const SET: u8 = 2;

/// A set-once `Py<T>` that `__clear__` can drop.
///
/// Written once while reachable ([`Slot::set`]) and cleared only by the garbage collector, which
/// calls `tp_clear` on unreachable objects only, so no reader can race with [`Slot::clear`].
pub(crate) struct Slot<T> {
    state: AtomicU8,
    value: UnsafeCell<Option<Py<T>>>,
}

// SAFETY: `value` is written once under the `state` handshake (EMPTY -> WRITING -> SET) and read
// only after SET is observed with Acquire ordering; `clear` runs only on unreachable objects (GC).
unsafe impl<T> Sync for Slot<T> {}

impl<T> Slot<T> {
    pub(crate) const fn empty() -> Self {
        Self {
            state: AtomicU8::new(EMPTY),
            value: UnsafeCell::new(None),
        }
    }

    pub(crate) fn with(value: Py<T>) -> Self {
        Self {
            state: AtomicU8::new(SET),
            value: UnsafeCell::new(Some(value)),
        }
    }

    /// Set the value; `false` (and `value` dropped) if it was set already.
    pub(crate) fn set(&self, value: Py<T>) -> bool {
        if self
            .state
            .compare_exchange(EMPTY, WRITING, Ordering::AcqRel, Ordering::Acquire)
            .is_err()
        {
            return false;
        }
        // SAFETY: the WRITING state gives this thread exclusive access; readers wait for SET.
        unsafe { *self.value.get() = Some(value) };
        self.state.store(SET, Ordering::Release);
        true
    }

    /// The value, once set.
    pub(crate) fn get(&self) -> Option<&Py<T>> {
        if self.state.load(Ordering::Acquire) != SET {
            return None;
        }
        // SAFETY: SET is final until `clear`, which only the GC calls on unreachable objects.
        unsafe { (*self.value.get()).as_ref() }
    }

    pub(crate) fn traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(self.get())
    }

    /// Drop the value (`__clear__`; the object is unreachable).
    pub(crate) fn clear(&self) {
        if self
            .state
            .compare_exchange(SET, WRITING, Ordering::AcqRel, Ordering::Acquire)
            .is_ok()
        {
            // SAFETY: see `set`; the object is unreachable, so nothing reads it concurrently.
            let value = unsafe { (*self.value.get()).take() };
            drop(value);
            self.state.store(EMPTY, Ordering::Release);
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Standard library types the kinds refer to
// ---------------------------------------------------------------------------------------------

/// A stdlib class, imported once.
pub(crate) fn std_type<'py>(
    py: Python<'py>,
    cell: &'static PyOnceLock<Py<PyType>>,
    module: &str,
    name: &str,
) -> PyResult<&'py Bound<'py, PyType>> {
    cell.get_or_try_init(py, || {
        py.import(module)?
            .getattr(name)?
            .cast_into::<PyType>()
            .map(Bound::unbind)
            .map_err(PyErr::from)
    })
    .map(|tp| tp.bind(py))
}

pub(crate) static UUID: PyOnceLock<Py<PyType>> = PyOnceLock::new();
pub(crate) static DECIMAL: PyOnceLock<Py<PyType>> = PyOnceLock::new();
pub(crate) static DATETIME: PyOnceLock<Py<PyType>> = PyOnceLock::new();
pub(crate) static DATE: PyOnceLock<Py<PyType>> = PyOnceLock::new();
pub(crate) static TIME: PyOnceLock<Py<PyType>> = PyOnceLock::new();
pub(crate) static TIMEDELTA: PyOnceLock<Py<PyType>> = PyOnceLock::new();

// ---------------------------------------------------------------------------------------------
// Kind
// ---------------------------------------------------------------------------------------------

/// JSON value types a kind takes without coercion (smart unions try exact matches first).
pub(crate) mod json_type {
    pub(crate) const NULL: u8 = 1;
    pub(crate) const BOOL: u8 = 1 << 1;
    pub(crate) const INT: u8 = 1 << 2;
    pub(crate) const FLOAT: u8 = 1 << 3;
    pub(crate) const STR: u8 = 1 << 4;
    pub(crate) const ARRAY: u8 = 1 << 5;
    pub(crate) const OBJECT: u8 = 1 << 6;
    pub(crate) const NUMBER: u8 = INT | FLOAT;
}

/// `isoformat(timespec=...)`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub(crate) enum Timespec {
    Auto,
    Hours,
    Minutes,
    Seconds,
    Milliseconds,
    Microseconds,
}

impl Timespec {
    fn parse(text: &str) -> PyResult<Self> {
        Ok(match text {
            "auto" => Self::Auto,
            "hours" => Self::Hours,
            "minutes" => Self::Minutes,
            "seconds" => Self::Seconds,
            "milliseconds" => Self::Milliseconds,
            "microseconds" => Self::Microseconds,
            _ => return Err(PyValueError::new_err(format!("unknown timespec {text:?}"))),
        })
    }
}

/// `EpochDatetime(unit=...)`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub(crate) enum Epoch {
    Seconds,
    Milliseconds,
}

/// The container a JSON array becomes.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub(crate) enum Collect {
    List,
    Tuple,
    Set,
    FrozenSet,
}

pub(crate) struct Text {
    pub(crate) tp: Py<PyType>,
    /// `str -> value`; a `ValueError` / `ArithmeticError` is a conversion error
    pub(crate) parse: Py<PyAny>,
    /// `value -> str`
    pub(crate) format: Py<PyAny>,
}

pub(crate) struct Enumeration {
    pub(crate) tp: Py<PyType>,
    /// By value: `(type(value), value) -> member`, so `true` / `1.0` never load an `IntEnum`.
    /// By name: `name -> member`.
    pub(crate) json: Py<PyDict>,
    /// The flat text (`str(value)`, or the name) -> member; `None` when two members share a text.
    pub(crate) text: Option<Py<PyDict>>,
    pub(crate) by_name: bool,
    /// The enum overrides `_missing_`: a by-value miss calls it with the (converted) value
    pub(crate) missing: bool,
}

pub(crate) struct Literal {
    pub(crate) values: Py<PyTuple>,
    /// `(type(value), value)` of every value, so `True` does not match `Literal[1]`
    pub(crate) json: Py<PyFrozenSet>,
    /// The flat text -> value (`None` -> `""`, `bool` -> `"1"`/`"0"`); `None` when two values
    /// share a text
    pub(crate) text: Option<Py<PyDict>>,
}

pub(crate) struct Union {
    pub(crate) members: Vec<Py<Kind>>,
    pub(crate) nullable: bool,
    pub(crate) discriminator: Option<Discriminator>,
}

/// `Annotated[A | B, Discriminator("kind")]`: the `Literal` tag field picks the member.
pub(crate) struct Discriminator {
    /// The tag field's attribute name
    pub(crate) name: Py<PyString>,
    /// Built from the members' fields once they are known (eagerly when possible, so a bad
    /// union is a `TypeError` at class creation)
    pub(crate) tags: std::sync::OnceLock<Tags>,
}

pub(crate) struct Tags {
    /// The tag field's stored key (the same in every member)
    pub(crate) key: Py<PyString>,
    /// Its fallback `load` keys (the same in every member)
    pub(crate) load: Vec<Py<PyString>>,
    /// `(type(tag), tag) -> member index`
    pub(crate) by_tag: Py<PyDict>,
    /// `one of ['cat', 'dog']`
    pub(crate) label: String,
}

pub(crate) enum Data {
    Str,
    Int,
    Float,
    Bool,
    /// JSON: canonical text, or hex (`UuidHex`); flat: hex
    Uuid {
        hex: bool,
    },
    /// ISO text (`isoformat(sep, timespec)`), or a number of seconds / milliseconds
    Datetime {
        timespec: Timespec,
        sep: char,
        epoch: Option<Epoch>,
    },
    Date,
    Time {
        timespec: Timespec,
    },
    /// A number of seconds
    Timedelta,
    /// Text, or a JSON number (`DecimalAsNumber`)
    Decimal {
        number: bool,
    },
    /// Padded base64 in JSON, unpadded base64url in the flat form
    Bytes,
    Text(Box<Text>),
    Enum(Box<Enumeration>),
    Literal(Box<Literal>),
    Optional(Py<Kind>),
    Sequence {
        item: Py<Kind>,
        collect: Collect,
    },
    Tuple(Vec<Py<Kind>>),
    Dict(Py<Kind>),
    Model(Slot<ModelCore>),
    Union(Box<Union>),
    /// A user converter: its `to_json` / `from_json` (and `to_str` / `from_str` when `flat`)
    Python {
        converter: Py<PyAny>,
        flat: bool,
    },
    Lazy(Slot<KindCell>),
}

/// One compiled annotation.
#[pyclass(frozen, module = "aiogram._core")]
pub struct Kind {
    pub(crate) data: Data,
    pub(crate) label: String,
    pub(crate) flat: bool,
    /// [`json_type`] bits of the JSON values taken without coercion
    pub(crate) json_types: u8,
    /// Python classes of the values taken without coercion (dump side of a smart union)
    pub(crate) py_types: Vec<Py<PyType>>,
}

impl Kind {
    fn new(
        data: Data,
        label: String,
        flat: bool,
        json_types: u8,
        py_types: Vec<Py<PyType>>,
    ) -> Self {
        Self {
            data,
            label,
            flat,
            json_types,
            py_types,
        }
    }

    /// The model core of a `Data::Model` kind.
    pub(crate) fn core(&self) -> Option<&Py<ModelCore>> {
        match &self.data {
            Data::Model(core) => core.get(),
            _ => None,
        }
    }

    /// The kind a `Data::Lazy` refers to; `RuntimeError` before its cell is set.
    pub(crate) fn resolved<'a>(&'a self, py: Python<'_>) -> PyResult<&'a Kind> {
        match &self.data {
            Data::Lazy(cell) => {
                let cell = cell
                    .get()
                    .ok_or_else(|| PyRuntimeError::new_err("lazy kind cleared"))?;
                let kind = cell.get().kind.get().ok_or_else(|| {
                    PyRuntimeError::new_err(format!("{} is not defined yet", self.label))
                })?;
                let _ = py;
                Ok(kind.get())
            }
            _ => Ok(self),
        }
    }
}

fn scalar(py: Python<'_>, data: Data, label: &str, json_types: u8, tp: &Bound<'_, PyType>) -> Kind {
    // every scalar has a flat form; datetime / date / time use ISO 8601 basic there (brief 12)
    let flat = true;
    let _ = py;
    Kind::new(
        data,
        label.to_owned(),
        flat,
        json_types,
        vec![tp.clone().unbind()],
    )
}

fn literal_text(value: &Bound<'_, PyAny>) -> PyResult<String> {
    if value.is_none() {
        return Ok(String::new());
    }
    if let Ok(flag) = value.cast::<pyo3::types::PyBool>() {
        return Ok(String::from(if flag.is_true() { "1" } else { "0" }));
    }
    Ok(value.str()?.to_string())
}

fn type_and_value<'py>(value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyTuple>> {
    PyTuple::new(value.py(), [value.get_type().into_any(), value.clone()])
}

fn json_type_of(value: &Bound<'_, PyAny>) -> u8 {
    use json_type::*;
    if value.is_none() {
        NULL
    } else if value.is_instance_of::<pyo3::types::PyBool>() {
        BOOL
    } else if value.is_instance_of::<pyo3::types::PyInt>() {
        INT
    } else if value.is_instance_of::<pyo3::types::PyFloat>() {
        FLOAT
    } else if value.is_instance_of::<PyString>() {
        STR
    } else {
        0
    }
}

#[pymethods]
impl Kind {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        for tp in &self.py_types {
            visit.call(tp)?;
        }
        match &self.data {
            Data::Str
            | Data::Int
            | Data::Float
            | Data::Bool
            | Data::Uuid { .. }
            | Data::Datetime { .. }
            | Data::Date
            | Data::Time { .. }
            | Data::Timedelta
            | Data::Decimal { .. }
            | Data::Bytes => {}
            Data::Text(text) => {
                visit.call(&text.tp)?;
                visit.call(&text.parse)?;
                visit.call(&text.format)?;
            }
            Data::Enum(enumeration) => {
                visit.call(&enumeration.tp)?;
                visit.call(&enumeration.json)?;
                visit.call(&enumeration.text)?;
            }
            Data::Literal(literal) => {
                visit.call(&literal.values)?;
                visit.call(&literal.json)?;
                visit.call(&literal.text)?;
            }
            Data::Optional(inner) | Data::Dict(inner) | Data::Sequence { item: inner, .. } => {
                visit.call(inner)?;
            }
            Data::Tuple(items) => {
                for item in items {
                    visit.call(item)?;
                }
            }
            Data::Model(core) => core.traverse(&visit)?,
            Data::Union(union) => {
                for member in &union.members {
                    visit.call(member)?;
                }
                if let Some(discriminator) = &union.discriminator {
                    visit.call(&discriminator.name)?;
                    if let Some(tags) = discriminator.tags.get() {
                        visit.call(&tags.key)?;
                        for key in &tags.load {
                            visit.call(key)?;
                        }
                        visit.call(&tags.by_tag)?;
                    }
                }
            }
            Data::Python { converter, .. } => visit.call(converter)?,
            Data::Lazy(cell) => cell.traverse(&visit)?,
        }
        Ok(())
    }

    fn __clear__(&self) {
        match &self.data {
            Data::Model(core) => core.clear(),
            Data::Lazy(cell) => cell.clear(),
            _ => {}
        }
    }

    fn __repr__(&self) -> String {
        format!("<Kind {}>", self.label)
    }

    #[getter]
    fn label(&self) -> &str {
        &self.label
    }

    #[getter]
    fn flat(&self) -> bool {
        self.flat
    }

    #[staticmethod]
    fn str_(py: Python<'_>) -> Self {
        scalar(
            py,
            Data::Str,
            "str",
            json_type::STR,
            &py.get_type::<PyString>(),
        )
    }

    #[staticmethod]
    fn int_(py: Python<'_>) -> Self {
        scalar(
            py,
            Data::Int,
            "int",
            json_type::INT,
            &py.get_type::<pyo3::types::PyInt>(),
        )
    }

    #[staticmethod]
    fn float_(py: Python<'_>) -> Self {
        scalar(
            py,
            Data::Float,
            "float",
            json_type::FLOAT,
            &py.get_type::<pyo3::types::PyFloat>(),
        )
    }

    #[staticmethod]
    fn bool_(py: Python<'_>) -> Self {
        scalar(
            py,
            Data::Bool,
            "bool",
            json_type::BOOL,
            &py.get_type::<pyo3::types::PyBool>(),
        )
    }

    #[staticmethod]
    #[pyo3(signature = (*, hex = false))]
    fn uuid(py: Python<'_>, hex: bool) -> PyResult<Self> {
        let tp = std_type(py, &UUID, "uuid", "UUID")?;
        Ok(scalar(py, Data::Uuid { hex }, "UUID", json_type::STR, tp))
    }

    #[staticmethod]
    #[pyo3(signature = (*, timespec = "auto", sep = "T", epoch = None))]
    fn datetime(py: Python<'_>, timespec: &str, sep: &str, epoch: Option<&str>) -> PyResult<Self> {
        let mut chars = sep.chars();
        let (Some(sep), None) = (chars.next(), chars.next()) else {
            return Err(PyValueError::new_err("sep must be one character"));
        };
        if !sep.is_ascii() {
            return Err(PyValueError::new_err("sep must be an ASCII character"));
        }
        let epoch = match epoch {
            None => None,
            Some("s") => Some(Epoch::Seconds),
            Some("ms") => Some(Epoch::Milliseconds),
            Some(other) => {
                return Err(PyValueError::new_err(format!(
                    "unknown epoch unit {other:?}"
                )));
            }
        };
        let json = if epoch.is_some() {
            json_type::NUMBER
        } else {
            json_type::STR
        };
        let tp = std_type(py, &DATETIME, "datetime", "datetime")?;
        Ok(scalar(
            py,
            Data::Datetime {
                timespec: Timespec::parse(timespec)?,
                sep,
                epoch,
            },
            "datetime",
            json,
            tp,
        ))
    }

    #[staticmethod]
    fn date(py: Python<'_>) -> PyResult<Self> {
        let tp = std_type(py, &DATE, "datetime", "date")?;
        Ok(scalar(py, Data::Date, "date", json_type::STR, tp))
    }

    #[staticmethod]
    #[pyo3(signature = (*, timespec = "auto"))]
    fn time(py: Python<'_>, timespec: &str) -> PyResult<Self> {
        let tp = std_type(py, &TIME, "datetime", "time")?;
        Ok(scalar(
            py,
            Data::Time {
                timespec: Timespec::parse(timespec)?,
            },
            "time",
            json_type::STR,
            tp,
        ))
    }

    #[staticmethod]
    fn timedelta(py: Python<'_>) -> PyResult<Self> {
        let tp = std_type(py, &TIMEDELTA, "datetime", "timedelta")?;
        Ok(scalar(
            py,
            Data::Timedelta,
            "timedelta",
            json_type::NUMBER,
            tp,
        ))
    }

    #[staticmethod]
    #[pyo3(signature = (*, number = false))]
    fn decimal(py: Python<'_>, number: bool) -> PyResult<Self> {
        let tp = std_type(py, &DECIMAL, "decimal", "Decimal")?;
        let json = if number {
            json_type::NUMBER
        } else {
            json_type::STR
        };
        Ok(scalar(py, Data::Decimal { number }, "Decimal", json, tp))
    }

    #[staticmethod]
    fn bytes_(py: Python<'_>) -> Self {
        scalar(
            py,
            Data::Bytes,
            "bytes",
            json_type::STR,
            &py.get_type::<pyo3::types::PyBytes>(),
        )
    }

    #[staticmethod]
    #[pyo3(signature = (tp, parse, format, *, flat))]
    fn text(
        tp: Bound<'_, PyType>,
        parse: Bound<'_, PyAny>,
        format: Bound<'_, PyAny>,
        flat: bool,
    ) -> PyResult<Self> {
        let label = tp.name()?.to_string();
        Ok(Kind::new(
            Data::Text(Box::new(Text {
                tp: tp.clone().unbind(),
                parse: parse.unbind(),
                format: format.unbind(),
            })),
            label,
            flat,
            json_type::STR,
            vec![tp.unbind()],
        ))
    }

    #[staticmethod]
    #[pyo3(signature = (tp, *, by_name = false, missing = false))]
    fn r#enum(tp: Bound<'_, PyType>, by_name: bool, missing: bool) -> PyResult<Self> {
        let py = tp.py();
        let json = PyDict::new(py);
        let text = PyDict::new(py);
        let mut json_types = 0;
        let mut count = 0usize;
        for member in tp.try_iter()? {
            let member = member?;
            count += 1;
            if by_name {
                let name = member.getattr(pyo3::intern!(py, "name"))?;
                json.set_item(&name, &member)?;
                text.set_item(&name, &member)?;
                json_types |= json_type::STR;
            } else {
                let value = member.getattr(pyo3::intern!(py, "value"))?;
                json.set_item(type_and_value(&value)?, &member)?;
                text.set_item(value.str()?, &member)?;
                json_types |= json_type_of(&value);
            }
        }
        let flat = text.len() == count;
        let label = tp.name()?.to_string();
        Ok(Kind::new(
            Data::Enum(Box::new(Enumeration {
                tp: tp.clone().unbind(),
                json: json.unbind(),
                text: flat.then(|| text.unbind()),
                by_name,
                missing: missing && !by_name,
            })),
            label,
            flat,
            json_types,
            vec![tp.unbind()],
        ))
    }

    #[staticmethod]
    fn literal(values: Bound<'_, PyAny>) -> PyResult<Self> {
        let py = values.py();
        let values = PyTuple::new(py, values.try_iter()?.collect::<PyResult<Vec<_>>>()?)?;
        let mut pairs = Vec::with_capacity(values.len());
        let text = PyDict::new(py);
        let mut json_types = 0;
        let mut py_types: Vec<Py<PyType>> = Vec::new();
        let mut reprs = Vec::with_capacity(values.len());
        for value in values.iter() {
            pairs.push(type_and_value(&value)?);
            text.set_item(literal_text(&value)?, &value)?;
            json_types |= json_type_of(&value);
            let tp = value.get_type();
            if !py_types.iter().any(|known| known.bind(py).is(&tp)) {
                py_types.push(tp.unbind());
            }
            reprs.push(value.repr()?.to_string());
        }
        let flat = text.len() == values.len();
        Ok(Kind::new(
            Data::Literal(Box::new(Literal {
                json: PyFrozenSet::new(py, &pairs)?.unbind(),
                values: values.unbind(),
                text: flat.then(|| text.unbind()),
            })),
            format!("one of [{}]", reprs.join(", ")),
            flat,
            json_types,
            py_types,
        ))
    }

    #[staticmethod]
    fn optional(inner: Bound<'_, Kind>) -> PyResult<Self> {
        let py = inner.py();
        let kind = inner.get();
        // "" is None in the flat codec (3.x pack writes None as ""): an enum member or Literal
        // value whose text is "" would come back as None, so there is no flat form
        let empty_text = match &kind.data {
            Data::Enum(enumeration) => match &enumeration.text {
                Some(text) => text.bind(py).contains("")?,
                None => false,
            },
            Data::Literal(literal) => match &literal.text {
                Some(text) => text.bind(py).contains("")?,
                None => false,
            },
            // `b""` packs as `""` too
            Data::Bytes => true,
            _ => false,
        };
        let mut py_types: Vec<Py<PyType>> =
            kind.py_types.iter().map(|tp| tp.clone_ref(py)).collect();
        py_types.push(py.None().bind(py).get_type().unbind());
        Ok(Kind::new(
            Data::Optional(inner.clone().unbind()),
            format!("{} | None", kind.label),
            kind.flat && !empty_text,
            kind.json_types | json_type::NULL,
            py_types,
        ))
    }

    #[staticmethod]
    fn sequence(item: Bound<'_, Kind>, container: Bound<'_, PyType>) -> PyResult<Self> {
        let py = item.py();
        let collect = if container.is(py.get_type::<PyList>()) {
            Collect::List
        } else if container.is(py.get_type::<PyTuple>()) {
            Collect::Tuple
        } else if container.is(py.get_type::<pyo3::types::PySet>()) {
            Collect::Set
        } else if container.is(py.get_type::<PyFrozenSet>()) {
            Collect::FrozenSet
        } else {
            return Err(PyTypeError::new_err(format!(
                "unsupported sequence container {}",
                container.name()?
            )));
        };
        let label = container.name()?.to_string();
        Ok(Kind::new(
            Data::Sequence {
                item: item.unbind(),
                collect,
            },
            label,
            false,
            json_type::ARRAY,
            vec![container.unbind()],
        ))
    }

    #[staticmethod]
    fn tuple_(items: Vec<Bound<'_, Kind>>) -> PyResult<Self> {
        let py = items
            .first()
            .map(Bound::py)
            .ok_or_else(|| PyTypeError::new_err("a fixed-length tuple needs at least one item"))?;
        Ok(Kind::new(
            Data::Tuple(items.into_iter().map(Bound::unbind).collect()),
            String::from("tuple"),
            false,
            json_type::ARRAY,
            vec![py.get_type::<PyTuple>().unbind()],
        ))
    }

    #[staticmethod]
    fn dict_(value: Bound<'_, Kind>) -> Self {
        let py = value.py();
        Kind::new(
            Data::Dict(value.unbind()),
            String::from("dict"),
            false,
            json_type::OBJECT,
            vec![py.get_type::<PyDict>().unbind()],
        )
    }

    #[staticmethod]
    pub(crate) fn model(core: Bound<'_, ModelCore>) -> PyResult<Self> {
        let py = core.py();
        let model = core.get();
        let label = model.qualname.clone();
        let tp = model.tp.clone_ref(py);
        let py_types = if model.is_dict() {
            vec![py.get_type::<PyDict>().unbind()]
        } else {
            vec![tp]
        };
        Ok(Kind::new(
            Data::Model(Slot::with(core.unbind())),
            label,
            false,
            json_type::OBJECT,
            py_types,
        ))
    }

    #[staticmethod]
    #[pyo3(signature = (members, *, nullable, discriminator = None))]
    fn union(
        members: Vec<Bound<'_, Kind>>,
        nullable: bool,
        discriminator: Option<Bound<'_, PyString>>,
    ) -> PyResult<Self> {
        let Some(py) = members.first().map(Bound::py) else {
            return Err(PyTypeError::new_err("a union needs at least one member"));
        };
        let mut labels: Vec<String> = members
            .iter()
            .map(|member| member.get().label.clone())
            .collect();
        if nullable {
            labels.push(String::from("None"));
        }
        let mut json_types = if nullable { json_type::NULL } else { 0 };
        let mut py_types: Vec<Py<PyType>> = Vec::new();
        for member in &members {
            json_types |= member.get().json_types;
            py_types.extend(member.get().py_types.iter().map(|tp| tp.clone_ref(py)));
        }
        if discriminator.is_some() && members.iter().any(|member| member.get().core().is_none()) {
            return Err(PyTypeError::new_err(format!(
                "{}: a Discriminator needs a union of models",
                labels.join(" | ")
            )));
        }
        let union = Union {
            members: members.into_iter().map(Bound::unbind).collect(),
            nullable,
            discriminator: discriminator.map(|name| Discriminator {
                name: name.unbind(),
                tags: std::sync::OnceLock::new(),
            }),
        };
        let kind = Kind::new(
            Data::Union(Box::new(union)),
            labels.join(" | "),
            false,
            json_types,
            py_types,
        );
        if let Data::Union(union) = &kind.data
            && union.discriminator.is_some()
            && union
                .members
                .iter()
                .all(|member| member.get().core().is_some_and(|core| core.get().ready()))
        {
            super::model::union_tags(py, union, &kind.label)?;
        }
        Ok(kind)
    }

    #[staticmethod]
    #[pyo3(signature = (converter, *, flat))]
    fn python(converter: Bound<'_, PyAny>, flat: bool) -> PyResult<Self> {
        let label = converter.get_type().name()?.to_string();
        Ok(Kind::new(
            Data::Python {
                converter: converter.unbind(),
                flat,
            },
            label,
            flat,
            0,
            Vec::new(),
        ))
    }

    #[staticmethod]
    fn lazy(cell: Bound<'_, KindCell>, label: String) -> Self {
        Kind::new(
            Data::Lazy(Slot::with(cell.unbind())),
            label,
            false,
            0,
            Vec::new(),
        )
    }
}

/// A kind set later: `type J = dict[str, J] | int` refers to itself.
#[pyclass(frozen, module = "aiogram._core")]
pub struct KindCell {
    pub(crate) kind: Slot<Kind>,
}

#[pymethods]
impl KindCell {
    #[new]
    fn new() -> Self {
        Self {
            kind: Slot::empty(),
        }
    }

    fn set(&self, kind: Bound<'_, Kind>) -> PyResult<()> {
        if self.kind.set(kind.unbind()) {
            Ok(())
        } else {
            Err(PyRuntimeError::new_err("KindCell is set already"))
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.kind.traverse(&visit)
    }

    fn __clear__(&self) {
        self.kind.clear();
    }
}

// ---------------------------------------------------------------------------------------------
// Field
// ---------------------------------------------------------------------------------------------

/// One field of a model, dataclass, NamedTuple or TypedDict.
#[pyclass(frozen, module = "aiogram._core")]
pub struct Field {
    /// The attribute name (`__dict__` / slot, `__init__` keyword, `__fields_set__`)
    pub(crate) name: Py<PyString>,
    /// The stored key (JSON object key; error locations)
    pub(crate) key: Py<PyString>,
    /// Fallback keys read on load, in order, after `key`
    pub(crate) load: Vec<Py<PyString>>,
    pub(crate) kind: Py<Kind>,
    pub(crate) default: Option<Py<PyAny>>,
    pub(crate) factory: Option<Py<PyAny>>,
    /// An `__init__` parameter
    pub(crate) init: bool,
    /// Keyword-only in `__init__`
    pub(crate) kw_only: bool,
    /// TypedDict: a `Required` key (a missing one is an error; others are left out)
    pub(crate) required: bool,
    /// The key came from `Key(...)` or `rename=` (the flat codec rejects it)
    pub(crate) keyed: bool,
}

impl Field {
    pub(crate) fn has_default(&self) -> bool {
        self.default.is_some() || self.factory.is_some()
    }
}

#[pymethods]
impl Field {
    #[new]
    #[pyo3(signature = (
        name, kind, *, key = None, load = Vec::new(), default = None, has_default = false,
        factory = None, init = true, kw_only = true, required = true, keyed = false,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        name: Bound<'_, PyString>,
        kind: Bound<'_, Kind>,
        key: Option<Bound<'_, PyString>>,
        load: Vec<Bound<'_, PyString>>,
        default: Option<Bound<'_, PyAny>>,
        has_default: bool,
        factory: Option<Bound<'_, PyAny>>,
        init: bool,
        kw_only: bool,
        required: bool,
        keyed: bool,
    ) -> PyResult<Self> {
        let py = name.py();
        if has_default && factory.is_some() {
            return Err(PyValueError::new_err(
                "a field takes a default or a factory, not both",
            ));
        }
        let intern = |text: &Bound<'_, PyString>| -> PyResult<Py<PyString>> {
            Ok(PyString::intern(py, text.to_str()?).unbind())
        };
        let default = if has_default {
            Some(default.unwrap_or_else(|| py.None().into_bound(py)).unbind())
        } else {
            None
        };
        Ok(Self {
            key: intern(key.as_ref().unwrap_or(&name))?,
            name: intern(&name)?,
            load: load.iter().map(intern).collect::<PyResult<_>>()?,
            kind: kind.unbind(),
            default,
            factory: factory.map(Bound::unbind),
            init,
            kw_only,
            required,
            keyed,
        })
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.name)?;
        visit.call(&self.key)?;
        for key in &self.load {
            visit.call(key)?;
        }
        visit.call(&self.kind)?;
        visit.call(&self.default)?;
        visit.call(&self.factory)
    }

    fn __repr__(&self, py: Python<'_>) -> String {
        format!(
            "<Field {}: {}>",
            self.name.bind(py).to_string_lossy(),
            self.kind.get().label
        )
    }

    #[getter]
    fn name(&self, py: Python<'_>) -> Py<PyString> {
        self.name.clone_ref(py)
    }

    #[getter]
    fn key(&self, py: Python<'_>) -> Py<PyString> {
        self.key.clone_ref(py)
    }

    #[getter]
    fn load<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        PyTuple::new(py, self.load.iter().map(|key| key.clone_ref(py)))
    }

    #[getter]
    fn kind(&self, py: Python<'_>) -> Py<Kind> {
        self.kind.clone_ref(py)
    }
}
