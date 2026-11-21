//! Compiled field types.

use pyo3::prelude::*;
use std::sync::OnceLock;

use pyo3::exceptions::PyRuntimeError;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyString, PyType};
use pyo3::{PyTraverseError, PyVisit};

use super::compile;
use super::schema::ModelSchema;

/// One compiled type; `converter` is the Python converter it came from (error `repr`s, and
/// the methods called for [`Data::Python`]).
pub(crate) struct Kind {
    pub(crate) data: Data,
    pub(crate) converter: Py<PyAny>,
}

pub(crate) enum Data {
    Str,
    Int,
    Float,
    Bool,
    /// `Decimal`, `Fraction`, `UUID`, `datetime`, `date`: text in both codecs
    Text(Box<Text>),
    Enum(Box<Enumeration>),
    Literal(Box<Literal>),
    Optional {
        inner: Box<Kind>,
        flat: bool,
    },
    Sequence {
        item: Box<Kind>,
        collect: Collect,
        tp: Py<PyType>,
    },
    Dict(Box<Kind>),
    TypedDict(Box<TypedDict>),
    Model(Box<Nested>),
    Union(Box<Union>),
    /// A user converter (`register_converter`, a `Converter` in `Annotated`, a subclass of a
    /// built-in that does not declare its own `kind`): call its methods.
    Python,
}

pub(crate) struct Text {
    pub(crate) tp: Py<PyType>,
    pub(crate) reject: Option<Py<PyType>>,
    pub(crate) parse: Py<PyAny>,
    pub(crate) to_text: Py<PyAny>,
    pub(crate) to_flat: Py<PyAny>,
    pub(crate) flat: bool,
    pub(crate) name: String,
}

pub(crate) struct Enumeration {
    pub(crate) tp: Py<PyType>,
    /// `_Enum._by_json`: `(type(value), value) -> member`, so `true` never loads an `IntEnum`
    pub(crate) by_json: Py<PyDict>,
    /// `_Enum._by_text`, `None` when the enum has no flat-string form
    pub(crate) by_text: Option<Py<PyDict>>,
    pub(crate) name: String,
}

pub(crate) struct Literal {
    /// `_Literal._json`: a set of `(type(value), value)`
    pub(crate) json: Py<PyAny>,
    /// `_Literal._text`, `None` when the literal has no flat-string form
    pub(crate) text: Option<Py<PyDict>>,
    /// `one of [...]`
    pub(crate) label: String,
}

/// The fields of a TypedDict, compiled on first use so a TypedDict may refer to itself.
pub(crate) struct TypedDict {
    pub(crate) fields: OnceLock<Vec<TypedDictField>>,
}

pub(crate) struct TypedDictField {
    pub(crate) key: String,
    pub(crate) name: Py<PyString>,
    pub(crate) kind: Kind,
    pub(crate) required: bool,
}

impl TypedDict {
    pub(crate) fn fields<'a>(
        &'a self,
        py: Python<'_>,
        converter: &Py<PyAny>,
    ) -> PyResult<&'a [TypedDictField]> {
        once(&self.fields, || {
            compile::typeddict_fields(converter.bind(py))
        })
        .map(Vec::as_slice)
    }
}

pub(crate) struct Union {
    pub(crate) members: Vec<Member>,
    pub(crate) nullable: bool,
    pub(crate) label: String,
    pub(crate) discriminator: Option<Discriminator>,
}

pub(crate) struct Member {
    pub(crate) kind: Kind,
    /// The JSON / Python value types this member takes without coercion (`_types`)
    pub(crate) json_types: Py<PyAny>,
    pub(crate) python_types: Py<PyAny>,
}

pub(crate) struct Discriminator {
    pub(crate) field: Py<PyString>,
    /// `_Union._tag_table()` and its "one of [...]" label, built on first use
    pub(crate) table: OnceLock<(Py<PyDict>, String)>,
}

/// The Python container a `_Sequence` builds from its JSON list.
#[derive(Clone, Copy)]
pub(crate) enum Collect {
    List,
    Tuple,
    Set,
    FrozenSet,
}

impl Collect {
    pub(crate) fn finish<'py>(self, list: Bound<'py, PyList>) -> PyResult<Bound<'py, PyAny>> {
        let py = list.py();
        Ok(match self {
            Self::List => list.into_any(),
            Self::Tuple => list.to_tuple().into_any(),
            Self::Set => PySet::new(py, list.iter())?.into_any(),
            Self::FrozenSet => PyFrozenSet::new(py, list.iter())?.into_any(),
        })
    }
}

/// A nested model, resolved on first use so self-referencing classes compile.
pub(crate) struct Nested {
    pub(crate) schema: OnceLock<Py<ModelSchema>>,
}

impl Nested {
    pub(crate) fn schema<'py>(
        &self,
        py: Python<'py>,
        converter: &Py<PyAny>,
    ) -> PyResult<&Bound<'py, ModelSchema>> {
        let schema = once(&self.schema, || {
            converter
                .bind(py)
                .call_method0(pyo3::intern!(py, "_rust_schema"))?
                .cast_into::<ModelSchema>()
                .map(Bound::unbind)
                .map_err(PyErr::from)
        })?;
        Ok(schema.bind(py))
    }
}

pub(crate) struct Field {
    /// The name for matching JSON keys
    pub(crate) key: String,
    /// The same name, interned, for dict lookups and attribute access
    pub(crate) name: Py<PyString>,
    pub(crate) kind: Kind,
    pub(crate) default: Option<Py<PyAny>>,
    pub(crate) factory: Option<Py<PyAny>>,
}

/// `OnceLock::get_or_try_init` (unstable): a racing thread's value is kept and the other dropped.
/// A plain `OnceLock` (not `PyOnceLock`) so `__traverse__` can read it without the Python API.
pub(crate) fn once<T>(cell: &OnceLock<T>, init: impl FnOnce() -> PyResult<T>) -> PyResult<&T> {
    if let Some(value) = cell.get() {
        return Ok(value);
    }
    let _ = cell.set(init()?);
    cell.get()
        .ok_or_else(|| PyRuntimeError::new_err("converter cache not initialised"))
}

/// Report every Python reference a kind tree holds, for the garbage collector: a built-in
/// converter and its `KindCore` reference each other.
pub(crate) fn traverse(kind: &Kind, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
    visit.call(&kind.converter)?;
    match &kind.data {
        Data::Str | Data::Int | Data::Float | Data::Bool | Data::Python => {}
        Data::Text(text) => {
            visit.call(&text.tp)?;
            visit.call(&text.reject)?;
            visit.call(&text.parse)?;
            visit.call(&text.to_text)?;
            visit.call(&text.to_flat)?;
        }
        Data::Enum(enumeration) => {
            visit.call(&enumeration.tp)?;
            visit.call(&enumeration.by_json)?;
            visit.call(&enumeration.by_text)?;
        }
        Data::Literal(literal) => {
            visit.call(&literal.json)?;
            visit.call(&literal.text)?;
        }
        Data::Optional { inner, .. } => traverse(inner, visit)?,
        Data::Sequence { item, tp, .. } => {
            traverse(item, visit)?;
            visit.call(tp)?;
        }
        Data::Dict(item) => traverse(item, visit)?,
        Data::TypedDict(typed) => {
            for field in typed.fields.get().into_iter().flatten() {
                visit.call(&field.name)?;
                traverse(&field.kind, visit)?;
            }
        }
        Data::Model(nested) => visit.call(nested.schema.get())?,
        Data::Union(union) => {
            for member in &union.members {
                traverse(&member.kind, visit)?;
                visit.call(&member.json_types)?;
                visit.call(&member.python_types)?;
            }
            if let Some(discriminator) = &union.discriminator {
                visit.call(&discriminator.field)?;
                visit.call(discriminator.table.get().map(|(table, _)| table))?;
            }
        }
    }
    Ok(())
}

pub(crate) fn traverse_field(field: &Field, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
    visit.call(&field.name)?;
    visit.call(&field.default)?;
    visit.call(&field.factory)?;
    traverse(&field.kind, visit)
}
