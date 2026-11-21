//! The Python-facing classes: [`ModelSchema`] (a model's field table) and [`KindCore`] (one
//! built-in converter), plus model loading, building and dumping.

use pyo3::exceptions::{PyAttributeError, PyValueError};
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PyType};
use pyo3::{PyTraverseError, PyVisit};

use super::errors::{self, at, expected};
use super::kind::{self, Field, Kind};
use super::load::Getter;
use super::{compile, dump, flat, json, load};

/// Compiled field table of one `ModelConverter` (`aiogram/utils/_converters.py`).
#[pyclass(frozen, module = "aiogram._core")]
pub struct ModelSchema {
    cls: Py<PyType>,
    qualname: String,
    is_model: bool,
    pub(crate) fields: Vec<Field>,
    /// `frozenset` of every field name, shared by loads that set all fields
    all_set: Py<PyFrozenSet>,
}

static OBJECT_NEW: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

fn field_at(py: Python<'_>, error: PyErr, field: &Field) -> PyErr {
    at(py, error, || Ok(format!(".{}", field.key)))
}

impl ModelSchema {
    /// `ModelConverter.from_json`.
    pub(crate) fn load<'py>(
        &self,
        py: Python<'py>,
        value: &Bound<'py, PyAny>,
        depth: u32,
    ) -> PyResult<Bound<'py, PyAny>> {
        errors::check_depth(depth)?;
        let getter = Getter::new(py, value)?;
        let mut values = Vec::with_capacity(self.fields.len());
        let mut set = Vec::with_capacity(self.fields.len());
        for field in &self.fields {
            let name = field.name.bind(py);
            let raw = getter.get(name)?;
            set.push(getter.contains(name, raw.is_some())?);
            values.push(match raw {
                Some(raw) => load::load(py, &raw, &field.kind, depth + 1)
                    .map_err(|e| field_at(py, e, field))?,
                None => self.default(py, field)?,
            });
        }
        self.build(py, values, &set, Some(value))
    }

    /// The default of a field missing from the input, or "field required".
    pub(crate) fn default<'py>(
        &self,
        py: Python<'py>,
        field: &Field,
    ) -> PyResult<Bound<'py, PyAny>> {
        match (&field.default, &field.factory) {
            (Some(default), _) => Ok(default.bind(py).clone()),
            (None, Some(factory)) => factory.bind(py).call0(),
            (None, None) => Err(errors::field_required(py, &field.key)),
        }
    }

    /// `ModelConverter._build`: a registered model gets its fields and the "set fields"
    /// record in its own `__dict__` (no `__init__`, no `__setattr__`); a dataclass or
    /// NamedTuple is called, and a `ValueError` from it becomes a `ConversionError`.
    pub(crate) fn build<'py>(
        &self,
        py: Python<'py>,
        values: Vec<Bound<'py, PyAny>>,
        set: &[bool],
        source: Option<&Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let cls = self.cls.bind(py);
        if !self.is_model {
            let kwargs = PyDict::new(py);
            for (field, value) in self.fields.iter().zip(values) {
                kwargs.set_item(field.name.bind(py), value)?;
            }
            return cls.call((), Some(&kwargs)).map_err(|error| {
                if !error.is_instance_of::<PyValueError>(py) {
                    return error;
                }
                let reason = error
                    .value(py)
                    .str()
                    .map(|text| text.to_string())
                    .unwrap_or_default();
                let wrapped = errors::conversion(py, &reason, source);
                wrapped.set_cause(py, Some(error));
                wrapped
            });
        }
        let object_new = OBJECT_NEW.get_or_try_init(py, || {
            py.get_type::<PyAny>().getattr("__new__").map(Bound::unbind)
        })?;
        let instance = object_new.bind(py).call1((cls,))?;
        let dict = instance
            .getattr(pyo3::intern!(py, "__dict__"))?
            .cast_into::<PyDict>()?;
        let mut names = Vec::new();
        for ((field, value), set) in self.fields.iter().zip(values).zip(set) {
            let name = field.name.bind(py);
            dict.set_item(name, value)?;
            if *set {
                names.push(name.clone());
            }
        }
        let fields_set = if names.len() == self.fields.len() {
            self.all_set.bind(py).clone()
        } else {
            PyFrozenSet::new(py, &names)?
        };
        dict.set_item(pyo3::intern!(py, "__fields_set__"), fields_set)?;
        Ok(instance)
    }

    fn check_instance(&self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<()> {
        if value.is_instance(self.cls.bind(py))? {
            Ok(())
        } else {
            Err(expected(
                py,
                &format!("a {} instance", self.qualname),
                value,
            ))
        }
    }

    /// `ModelConverter.to_json`.
    pub(crate) fn to_json<'py>(
        &self,
        py: Python<'py>,
        value: &Bound<'py, PyAny>,
        depth: u32,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.check_instance(py, value)?;
        Ok(self.dump_fields(py, value, false, depth)?.into_any())
    }

    /// `ModelConverter.dump`.
    fn dump_fields<'py>(
        &self,
        py: Python<'py>,
        value: &Bound<'py, PyAny>,
        exclude_unset: bool,
        depth: u32,
    ) -> PyResult<Bound<'py, PyDict>> {
        errors::check_depth(depth)?;
        let fields_set = if exclude_unset {
            match value.getattr(pyo3::intern!(py, "__fields_set__")) {
                Ok(fields_set) => Some(fields_set),
                Err(error) if error.is_instance_of::<PyAttributeError>(py) => None,
                Err(error) => return Err(error),
            }
        } else {
            None
        };
        let out = PyDict::new(py);
        for field in &self.fields {
            let name = field.name.bind(py);
            if let Some(fields_set) = &fields_set
                && !fields_set.contains(name)?
            {
                continue;
            }
            let attribute = value.getattr(name)?;
            let converted = dump::dump(py, &attribute, &field.kind, depth + 1)
                .map_err(|e| field_at(py, e, field))?;
            out.set_item(name, converted)?;
        }
        Ok(out)
    }
}

#[pymethods]
impl ModelSchema {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.cls)?;
        visit.call(&self.all_set)?;
        for field in &self.fields {
            kind::traverse_field(field, &visit)?;
        }
        Ok(())
    }

    #[new]
    fn new(converter: &Bound<'_, PyAny>) -> PyResult<Self> {
        let py = converter.py();
        let (fields, names) = compile::fields(converter)?;
        let cls = converter.getattr("tp")?.cast_into::<PyType>()?;
        Ok(Self {
            qualname: cls.getattr("__qualname__")?.extract()?,
            cls: cls.unbind(),
            is_model: converter.getattr("is_model")?.extract()?,
            fields,
            all_set: PyFrozenSet::new(py, &names)?.unbind(),
        })
    }

    /// `ModelConverter.from_json`: a JSON-shaped mapping -> instance.
    fn load_dict<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        self.load(value.py(), value, 0)
    }

    /// `ModelConverter.load_json`: JSON `bytes` / `bytearray` / `str` -> instance in one pass.
    fn load_json<'py>(&self, data: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        json::load_document(data.py(), data, self)
    }

    /// `ModelConverter.to_json`: instance -> JSON-shaped dict (validates the values).
    #[pyo3(name = "to_json")]
    fn py_to_json<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        self.to_json(value.py(), value, 0)
    }

    /// `ModelConverter.dump`.
    #[pyo3(signature = (value, *, exclude_unset = false))]
    fn dump<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        exclude_unset: bool,
    ) -> PyResult<Bound<'py, PyDict>> {
        self.dump_fields(value.py(), value, exclude_unset, 0)
    }

    /// `ModelConverter.from_flat`: callback-data parts (one string per field) -> instance.
    #[pyo3(name = "from_flat")]
    fn load_flat<'py>(&self, parts: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = parts.py();
        if parts.len()? != self.fields.len() {
            let given = py.get_type::<PyList>().call1((parts,))?;
            return Err(errors::conversion(
                py,
                &format!("expected {} parts", self.fields.len()),
                Some(&given),
            ));
        }
        let mut values = Vec::with_capacity(self.fields.len());
        for (field, part) in self.fields.iter().zip(parts.try_iter()?) {
            values
                .push(flat::from_str(py, &part?, &field.kind).map_err(|e| field_at(py, e, field))?);
        }
        let set = vec![true; values.len()];
        self.build(py, values, &set, Some(parts))
    }

    /// `ModelConverter.to_flat`: instance -> callback-data parts.
    fn to_flat<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyList>> {
        let py = value.py();
        self.check_instance(py, value)?;
        let parts = PyList::empty(py);
        for field in &self.fields {
            let attribute = value.getattr(field.name.bind(py))?;
            parts.append(
                flat::to_str(py, &attribute, &field.kind).map_err(|e| field_at(py, e, field))?,
            )?;
        }
        Ok(parts)
    }
}

/// The compiled core of one built-in converter (`_Str`, `_Sequence`, `_Union`...): its
/// `to_json` / `from_json` / `to_str` / `from_str` methods call these.
#[pyclass(frozen, module = "aiogram._core")]
pub struct KindCore {
    kind: Kind,
}

#[pymethods]
impl KindCore {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        kind::traverse(&self.kind, &visit)
    }

    #[new]
    fn new(converter: &Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(Self {
            kind: compile::kind(converter, true)?,
        })
    }

    #[pyo3(name = "from_json")]
    fn load_value<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        load::load(value.py(), value, &self.kind, 0)
    }

    fn to_json<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        dump::dump(value.py(), value, &self.kind, 0)
    }

    #[pyo3(name = "from_str")]
    fn load_str<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        flat::from_str(value.py(), value, &self.kind)
    }

    fn to_str<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        flat::to_str(value.py(), value, &self.kind)
    }
}
