//! Compiled field types.

use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyString, PyType};

use super::fallback::Fast;
use super::schema::ModelSchema;

/// One field type, compiled from the Python converter's `kind` tag.
pub(crate) enum Kind {
    Str,
    Int,
    Float,
    Bool,
    Optional {
        inner: Box<Kind>,
        flat: bool,
    },
    Enum {
        tp: Py<PyType>,
        /// `Enum._value2member_map_`
        by_value: Py<PyDict>,
        /// `_Enum._by_text`, `None` when the enum has no flat-string form
        by_text: Option<Py<PyDict>>,
    },
    Literal {
        /// `_Literal._json`: a set of `(type(value), value)`
        json: Py<PyAny>,
        /// `_Literal._text`, `None` when the literal has no flat-string form
        text: Option<Py<PyDict>>,
    },
    Sequence {
        item: Box<Kind>,
        collect: Collect,
    },
    Dict(Box<Kind>),
    Model(Box<Nested>),
    /// Any other converter (`Decimal`, `UUID`, `datetime`, unions, TypedDicts, user
    /// converters...): call it.
    Python(Py<PyAny>),
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
            // unhashable items raise here and fall back, so Python raises the same TypeError
            Self::Set => PySet::new(py, list.iter())?.into_any(),
            Self::FrozenSet => PyFrozenSet::new(py, list.iter())?.into_any(),
        })
    }
}

/// A nested model, resolved on first use so self-referencing classes compile.
pub(crate) struct Nested {
    pub(crate) converter: Py<PyAny>,
    pub(crate) schema: PyOnceLock<Py<ModelSchema>>,
}

impl Nested {
    pub(crate) fn schema<'py>(&self, py: Python<'py>) -> Fast<&Bound<'py, ModelSchema>> {
        let schema = self.schema.get_or_try_init(py, || {
            self.converter
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
