//! [`ModelCore`]: the field table and builder of one class (a `ModelBase` model, a dataclass, a
//! NamedTuple or a TypedDict). Its fields are set once by the resolver, possibly after the
//! [`Kind`](super::ir::Kind)s that refer to it were built (recursive and forward references).

use std::collections::HashMap;
use std::sync::OnceLock;

use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyString, PyTuple, PyType};
use pyo3::{PyTraverseError, PyVisit};

use super::construct;
use super::ir::{Data, Field, Tags, Union};

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub(crate) enum Build {
    /// A `ModelBase` class: `object.__new__`, generic setattr, `__fields_set__`, `__post_init__`
    Model,
    /// A dataclass or NamedTuple: `cls(**values)`
    Call,
    /// A TypedDict: a plain dict of the keys present
    Dict,
}

pub(crate) struct Fields {
    pub(crate) list: Vec<Py<Field>>,
    /// Stored key or fallback load key -> (field index, priority: 0 for the stored key, then
    /// 1, 2... for the `load` keys in order)
    pub(crate) index: HashMap<String, (usize, usize)>,
    /// `frozenset` of every attribute name, shared by loads that set every field
    pub(crate) all_set: Py<PyFrozenSet>,
    /// Indexes of the positional `__init__` parameters (`init` and not `kw_only`), in order
    pub(crate) positional: Vec<usize>,
}

#[pyclass(frozen, module = "aiogram._core.conv")]
pub struct ModelCore {
    pub(crate) tp: Py<PyType>,
    pub(crate) qualname: String,
    pub(crate) build: Build,
    pub(crate) post_init: bool,
    pub(crate) resolve: Option<Py<PyAny>>,
    pub(crate) fields: OnceLock<Fields>,
}

impl ModelCore {
    pub(crate) fn is_dict(&self) -> bool {
        self.build == Build::Dict
    }

    pub(crate) fn ready(&self) -> bool {
        self.fields.get().is_some()
    }

    /// The fields; calls `resolve` first when they are not set yet (it raises the
    /// "not fully defined" `NameError` when it cannot set them).
    pub(crate) fn fields(&self, py: Python<'_>) -> PyResult<&Fields> {
        if let Some(fields) = self.fields.get() {
            return Ok(fields);
        }
        if let Some(resolve) = &self.resolve {
            resolve.bind(py).call0()?;
        }
        self.fields
            .get()
            .ok_or_else(|| PyRuntimeError::new_err(format!("{} has no fields set", self.qualname)))
    }
}

#[pymethods]
impl ModelCore {
    #[new]
    #[pyo3(signature = (tp, *, build, post_init = false, resolve = None))]
    fn new(
        tp: Bound<'_, PyType>,
        build: &str,
        post_init: bool,
        resolve: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Self> {
        let build = match build {
            "model" => Build::Model,
            "call" => Build::Call,
            "dict" => Build::Dict,
            other => return Err(PyValueError::new_err(format!("unknown build {other:?}"))),
        };
        Ok(Self {
            qualname: tp.qualname()?.to_string(),
            tp: tp.unbind(),
            build,
            post_init,
            resolve: resolve.map(Bound::unbind),
            fields: OnceLock::new(),
        })
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.tp)?;
        visit.call(&self.resolve)?;
        if let Some(fields) = self.fields.get() {
            for field in &fields.list {
                visit.call(field)?;
            }
            visit.call(&fields.all_set)?;
        }
        Ok(())
    }

    fn __repr__(&self) -> String {
        format!("<ModelCore {}>", self.qualname)
    }

    #[getter]
    fn tp(&self, py: Python<'_>) -> Py<PyType> {
        self.tp.clone_ref(py)
    }

    #[getter(ready)]
    fn py_ready(&self) -> bool {
        self.ready()
    }

    fn set_fields(&self, py: Python<'_>, fields: Vec<Bound<'_, Field>>) -> PyResult<()> {
        let mut index = HashMap::new();
        let mut names = Vec::with_capacity(fields.len());
        let mut positional = Vec::new();
        for (position, field) in fields.iter().enumerate() {
            let spec = field.get();
            names.push(spec.name.clone_ref(py));
            if spec.init && !spec.kw_only {
                positional.push(position);
            }
            let keys = std::iter::once(&spec.key).chain(&spec.load);
            for (priority, key) in keys.enumerate() {
                let text = key.bind(py).to_str()?.to_owned();
                if let Some((other, _)) = index.insert(text.clone(), (position, priority)) {
                    let other = fields[other]
                        .get()
                        .name
                        .bind(py)
                        .to_string_lossy()
                        .into_owned();
                    return Err(PyTypeError::new_err(format!(
                        "{}: fields '{other}' and '{}' both read the key '{text}'",
                        self.qualname,
                        spec.name.bind(py).to_string_lossy()
                    )));
                }
            }
        }
        self.store(Fields {
            list: fields.into_iter().map(Bound::unbind).collect(),
            index,
            all_set: PyFrozenSet::new(py, &names)?.unbind(),
            positional,
        })
    }

    /// `ModelBase.__init__`: see `construct::init`.
    fn init(
        &self,
        instance: &Bound<'_, PyAny>,
        args: &Bound<'_, PyTuple>,
        kwargs: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        construct::init(instance.py(), self, instance, args, kwargs)
    }
}

impl ModelCore {
    fn store(&self, fields: Fields) -> PyResult<()> {
        self.fields.set(fields).map_err(|_| {
            PyRuntimeError::new_err(format!("{} has its fields set already", self.qualname))
        })
    }
}

/// The discriminator tag table of `union` (all members are models with their fields set):
/// `TypeError` when a member has no `Literal` tag field, the members store the tag under
/// different keys, or two members share a tag.
pub(crate) fn union_tags<'a>(py: Python<'_>, union: &'a Union, label: &str) -> PyResult<&'a Tags> {
    let Some(discriminator) = &union.discriminator else {
        return Err(PyRuntimeError::new_err("not a discriminated union"));
    };
    if let Some(tags) = discriminator.tags.get() {
        return Ok(tags);
    }
    let name = discriminator.name.bind(py);
    let by_tag = PyDict::new(py);
    let mut key: Option<Py<PyString>> = None;
    let mut load: Vec<Py<PyString>> = Vec::new();
    let mut reprs = Vec::new();
    for (position, member) in union.members.iter().enumerate() {
        let core = member.get().core().ok_or_else(|| {
            PyTypeError::new_err(format!("{label}: a Discriminator needs a union of models"))
        })?;
        let fields = core.get().fields(py)?;
        let field = fields
            .list
            .iter()
            .map(|field| field.get())
            .find(|field| field.name.bind(py).as_any().eq(name).unwrap_or(false));
        let literal = field.and_then(|field| match &field.kind.get().data {
            Data::Literal(literal) => Some((field, literal)),
            _ => None,
        });
        let Some((field, literal)) = literal else {
            return Err(PyTypeError::new_err(format!(
                "{label}: every member needs a Literal '{}' field",
                name.to_string_lossy()
            )));
        };
        let same_load = |known: &[Py<PyString>]| -> PyResult<bool> {
            if known.len() != field.load.len() {
                return Ok(false);
            }
            for (a, b) in known.iter().zip(&field.load) {
                if !a.bind(py).as_any().eq(b.bind(py))? {
                    return Ok(false);
                }
            }
            Ok(true)
        };
        match &key {
            None => {
                key = Some(field.key.clone_ref(py));
                load = field.load.iter().map(|k| k.clone_ref(py)).collect();
            }
            Some(known) if known.bind(py).as_any().eq(field.key.bind(py))? && same_load(&load)? => {
            }
            Some(_) => {
                return Err(PyTypeError::new_err(format!(
                    "{label}: the members store the tag '{}' under different keys",
                    name.to_string_lossy()
                )));
            }
        }
        for value in literal.values.bind(py).iter() {
            let pair = PyTuple::new(py, [value.get_type().into_any(), value.clone()])?;
            if by_tag.contains(&pair)? {
                return Err(PyTypeError::new_err(format!(
                    "{label}: tag {} is used by more than one member",
                    value.repr()?
                )));
            }
            by_tag.set_item(pair, position)?;
            reprs.push(value.repr()?.to_string());
        }
    }
    let key = key.ok_or_else(|| PyTypeError::new_err(format!("{label}: a union needs members")))?;
    let _ = discriminator.tags.set(Tags {
        key,
        load,
        by_tag: by_tag.unbind(),
        label: format!("one of [{}]", reprs.join(", ")),
    });
    discriminator
        .tags
        .get()
        .ok_or_else(|| PyRuntimeError::new_err("discriminator tags not set"))
}
