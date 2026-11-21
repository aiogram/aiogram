//! The Python-facing codecs: [`JsonSchema`] and [`FlatSchema`] of a class, [`JsonCodec`] of any
//! kind. Each method is a thin wrapper: the walkers do the work and return [`ValError`]s, and the
//! one Python `ConversionError` is built here ([`materialize`]), titled `<action> <label>`.

use std::sync::OnceLock;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList, PyString, PyTuple};
use pyo3::{PyTraverseError, PyVisit};

use super::errors::{Ctx, ValError, materialize};
use super::ir::Kind;
use super::model::ModelCore;
use super::{flat, json};

fn fail(py: Python<'_>, action: &str, kind: &Kind, error: ValError) -> PyErr {
    materialize(py, &format!("{action} {}", kind.label), error)
}

/// The JSON codec of one class: `json_schema(cls)`.
#[pyclass(frozen, generic, module = "aiogram._core.conv")]
pub struct JsonSchema {
    core: Py<ModelCore>,
    kind: Py<Kind>,
}

#[pymethods]
impl JsonSchema {
    #[new]
    fn new(core: Bound<'_, ModelCore>) -> PyResult<Self> {
        let py = core.py();
        let kind = Py::new(py, Kind::model(core.clone())?)?;
        Ok(Self {
            core: core.unbind(),
            kind,
        })
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.core)?;
        visit.call(&self.kind)
    }

    fn __repr__(&self) -> String {
        format!("<JsonSchema {}>", self.core.get().qualname)
    }

    #[getter]
    fn core(&self, py: Python<'_>) -> Py<ModelCore> {
        self.core.clone_ref(py)
    }

    /// Attribute name -> (stored key, fallback load keys).
    #[getter]
    fn keys<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let keys = PyDict::new(py);
        for field in &self.core.get().fields(py)?.list {
            let field = field.get();
            let load = PyTuple::new(py, field.load.iter().map(|key| key.clone_ref(py)))?;
            keys.set_item(&field.name, (field.key.clone_ref(py), load))?;
        }
        Ok(keys)
    }

    fn load<'py>(&self, data: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = data.py();
        let kind = self.kind.get();
        json::load::load(py, data, kind, Ctx::new(false)).map_err(|e| fail(py, "loading", kind, e))
    }

    fn load_json<'py>(&self, data: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = data.py();
        let kind = self.kind.get();
        json::parse::load_json(py, data, kind).map_err(|e| fail(py, "loading", kind, e))
    }

    #[pyo3(signature = (obj, *, exclude_unset = false))]
    fn dump<'py>(
        &self,
        obj: &Bound<'py, PyAny>,
        exclude_unset: bool,
    ) -> PyResult<Bound<'py, PyAny>> {
        let py = obj.py();
        let kind = self.kind.get();
        let ctx = Ctx {
            exclude_unset,
            ..Ctx::new(false)
        };
        json::dump::dump(py, obj, kind, ctx).map_err(|e| fail(py, "dumping", kind, e))
    }

    #[pyo3(signature = (obj, *, exclude_unset = false))]
    fn dump_json<'py>(
        &self,
        obj: &Bound<'py, PyAny>,
        exclude_unset: bool,
    ) -> PyResult<Bound<'py, PyBytes>> {
        let py = obj.py();
        let kind = self.kind.get();
        let ctx = Ctx {
            exclude_unset,
            ..Ctx::new(false)
        };
        let bytes =
            json::write::dump_json(py, obj, kind, ctx).map_err(|e| fail(py, "dumping", kind, e))?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Check and dump some fields (a typed patch): attribute names in, stored keys out.
    fn dump_fields<'py>(&self, values: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyDict>> {
        let py = values.py();
        json::dump::dump_fields(py, self.core.get(), values)
            .map_err(|e| fail(py, "dumping", self.kind.get(), e))
    }
}

/// The positional flat-string codec of one class (callback data): `flat_schema(cls)`.
#[pyclass(frozen, generic, module = "aiogram._core.conv")]
pub struct FlatSchema {
    core: Py<ModelCore>,
    kind: Py<Kind>,
    /// `flat::check` passed (done at construction when the fields are known, else on first use)
    checked: OnceLock<()>,
}

impl FlatSchema {
    fn checked(&self, py: Python<'_>) -> PyResult<()> {
        if self.checked.get().is_none() {
            flat::check(py, self.core.get())?;
            let _ = self.checked.set(());
        }
        Ok(())
    }
}

#[pymethods]
impl FlatSchema {
    #[new]
    fn new(core: Bound<'_, ModelCore>) -> PyResult<Self> {
        let py = core.py();
        let kind = Py::new(py, Kind::model(core.clone())?)?;
        let schema = Self {
            core: core.unbind(),
            kind,
            checked: OnceLock::new(),
        };
        if schema.core.get().ready() {
            schema.checked(py)?;
        }
        Ok(schema)
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.core)?;
        visit.call(&self.kind)
    }

    fn __repr__(&self) -> String {
        format!("<FlatSchema {}>", self.core.get().qualname)
    }

    #[getter]
    fn core(&self, py: Python<'_>) -> Py<ModelCore> {
        self.core.clone_ref(py)
    }

    fn load<'py>(&self, parts: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = parts.py();
        self.checked(py)?;
        flat::load_parts(py, self.core.get(), parts)
            .map_err(|e| fail(py, "loading", self.kind.get(), e))
    }

    fn dump<'py>(&self, obj: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyList>> {
        let py = obj.py();
        self.checked(py)?;
        flat::dump_parts(py, self.core.get(), obj)
            .map_err(|e| fail(py, "dumping", self.kind.get(), e))
    }
}

/// The JSON (and flat) codec of any kind: `json_codec(list[int])`.
#[pyclass(frozen, module = "aiogram._core.conv")]
pub struct JsonCodec {
    kind: Py<Kind>,
}

#[pymethods]
impl JsonCodec {
    #[new]
    fn new(kind: Bound<'_, Kind>) -> Self {
        Self {
            kind: kind.unbind(),
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.kind)
    }

    fn __repr__(&self) -> String {
        format!("<JsonCodec {}>", self.kind.get().label)
    }

    #[getter]
    fn kind(&self, py: Python<'_>) -> Py<Kind> {
        self.kind.clone_ref(py)
    }

    fn load<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = value.py();
        let kind = self.kind.get();
        json::load::load(py, value, kind, Ctx::new(false)).map_err(|e| fail(py, "loading", kind, e))
    }

    fn load_json<'py>(&self, data: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = data.py();
        let kind = self.kind.get();
        json::parse::load_json(py, data, kind).map_err(|e| fail(py, "loading", kind, e))
    }

    fn dump<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = value.py();
        let kind = self.kind.get();
        json::dump::dump(py, value, kind, Ctx::new(false)).map_err(|e| fail(py, "dumping", kind, e))
    }

    fn dump_json<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyBytes>> {
        let py = value.py();
        let kind = self.kind.get();
        let bytes = json::write::dump_json(py, value, kind, Ctx::new(false))
            .map_err(|e| fail(py, "dumping", kind, e))?;
        Ok(PyBytes::new(py, &bytes))
    }

    fn load_flat<'py>(&self, text: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = text.py();
        let kind = self.kind.get();
        if !kind.flat {
            return Err(PyTypeError::new_err(format!(
                "{} has no flat-string form",
                kind.label
            )));
        }
        flat::load(py, text, kind).map_err(|e| fail(py, "loading", kind, e))
    }

    fn dump_flat<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyString>> {
        let py = value.py();
        let kind = self.kind.get();
        if !kind.flat {
            return Err(PyTypeError::new_err(format!(
                "{} has no flat-string form",
                kind.label
            )));
        }
        flat::dump(py, value, kind).map_err(|e| fail(py, "dumping", kind, e))
    }
}
