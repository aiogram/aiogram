//! [`ModelSchema`]: the compiled field table, the Python-facing class, and instance building.

use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyFrozenSet, PyString, PyType};

use super::fallback::{Fallback, Fast};
use super::kind::Field;
use super::{compile, dict, flat, json};

/// Compiled field table of one `ModelConverter` (`aiogram/utils/_converters.py`).
#[pyclass(frozen, module = "aiogram._core")]
pub struct ModelSchema {
    converter: Py<PyAny>,
    cls: Py<PyType>,
    is_model: bool,
    pub(crate) fields: Vec<Field>,
    /// `frozenset` of every field name, shared by loads that set all fields
    all_set: Py<PyFrozenSet>,
}

static OBJECT_NEW: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

impl ModelSchema {
    pub(crate) fn cls<'py>(&self, py: Python<'py>) -> &Bound<'py, PyType> {
        self.cls.bind(py)
    }

    /// Build the instance the way `ModelConverter._build` does.
    pub(crate) fn build<'py>(
        &self,
        py: Python<'py>,
        values: Vec<Option<Bound<'py, PyAny>>>,
    ) -> Fast<Bound<'py, PyAny>> {
        let dict = PyDict::new(py);
        let mut set = Vec::new();
        let mut all = true;
        for (field, value) in self.fields.iter().zip(values) {
            let name = field.name.bind(py);
            match value {
                Some(value) => {
                    dict.set_item(name, value)?;
                    if self.is_model {
                        set.push(name.clone());
                    }
                }
                None => {
                    all = false;
                    match (&field.default, &field.factory) {
                        (Some(default), _) => dict.set_item(name, default.bind(py))?,
                        (None, Some(factory)) => dict.set_item(name, factory.bind(py).call0()?)?,
                        (None, None) => return Err(Fallback), // required: Python raises
                    }
                }
            }
        }
        let cls = self.cls.bind(py);
        if !self.is_model {
            // dataclass / NamedTuple; a ValueError from __post_init__ falls back too, so
            // Python wraps it identically
            return Ok(cls.call((), Some(&dict))?);
        }
        let fields_set = if all {
            self.all_set.bind(py).clone()
        } else {
            PyFrozenSet::new(py, &set)?
        };
        dict.set_item(pyo3::intern!(py, "__fields_set__"), fields_set)?;
        let object_new = OBJECT_NEW.get_or_try_init(py, || {
            py.get_type::<PyAny>().getattr("__new__").map(Bound::unbind)
        })?;
        let instance = object_new.bind(py).call1((cls,))?;
        instance.setattr(pyo3::intern!(py, "__dict__"), dict)?;
        Ok(instance)
    }

    fn run<'py>(
        &self,
        fast: Fast<Bound<'py, PyAny>>,
        fallback: &Bound<'py, PyString>,
        arg: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        match fast {
            Ok(result) => Ok(result),
            Err(Fallback) => self.converter.bind(arg.py()).call_method1(fallback, (arg,)),
        }
    }
}

#[pymethods]
impl ModelSchema {
    #[new]
    fn new(converter: &Bound<'_, PyAny>) -> PyResult<Self> {
        let py = converter.py();
        let (fields, names) = compile::fields(converter)?;
        Ok(Self {
            converter: converter.clone().unbind(),
            cls: converter.getattr("tp")?.cast_into::<PyType>()?.unbind(),
            is_model: converter.getattr("is_model")?.extract()?,
            fields,
            all_set: PyFrozenSet::new(py, &names)?.unbind(),
        })
    }

    /// `ModelConverter.from_json`: a JSON-shaped dict -> instance.
    fn load_dict<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = value.py();
        self.run(
            dict::load_model(py, value, self),
            pyo3::intern!(py, "_py_from_json"),
            value,
        )
    }

    /// `ModelConverter.load_json`: JSON `bytes` / `str` -> instance in one pass.
    fn load_json<'py>(&self, data: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = data.py();
        self.run(
            json::load_document(py, data, self),
            pyo3::intern!(py, "_py_load_json"),
            data,
        )
    }

    /// `ModelConverter.from_flat`: callback-data parts -> instance.
    #[pyo3(name = "from_flat")]
    fn load_flat<'py>(&self, parts: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = parts.py();
        self.run(
            flat::from_parts(py, parts, self),
            pyo3::intern!(py, "_py_from_flat"),
            parts,
        )
    }

    /// `ModelConverter.to_flat`: instance -> callback-data parts.
    fn to_flat<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = value.py();
        self.run(
            flat::to_parts(py, value, self).map(Bound::into_any),
            pyo3::intern!(py, "_py_to_flat"),
            value,
        )
    }
}
