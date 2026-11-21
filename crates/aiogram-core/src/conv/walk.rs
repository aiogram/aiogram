//! Walker plumbing shared by every codec: error collection, mapping access, dict iteration that
//! is safe on free-threaded builds, and the smart-union member trials.

use std::cell::RefCell;

use pyo3::exceptions::PyStopIteration;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple, PyType};

use super::errors::{self, Ctx, Line, MAX_ERRORS, VResult, ValError};
use super::ir::{Kind, json_type, std_type};

/// The errors of one container in collecting mode.
pub(crate) struct Errors(Option<ValError>);

impl Errors {
    pub(crate) const fn new() -> Self {
        Self(None)
    }

    /// Record `error`; `Err` when the walk must stop now: fast mode, a fatal error, or
    /// [`MAX_ERRORS`] lines.
    pub(crate) fn push(&mut self, error: ValError, ctx: Ctx) -> VResult<()> {
        let merged = match self.0.take() {
            None => error,
            Some(known) => known.extend(error),
        };
        if ctx.fast || matches!(merged, ValError::Fatal(_)) || merged.len() >= MAX_ERRORS {
            return Err(merged);
        }
        self.0 = Some(merged);
        Ok(())
    }

    pub(crate) fn finish(self) -> VResult<()> {
        self.0.map_or(Ok(()), Err)
    }
}

/// `f(key, value)` for every item of `dict`, under the dict's critical section on free-threaded
/// builds; the first `Err` stops the iteration.
pub(crate) fn dict_for_each<'py>(
    dict: &Bound<'py, PyDict>,
    f: impl Fn(Bound<'py, PyAny>, Bound<'py, PyAny>) -> VResult<()>,
) -> VResult<()> {
    let stopped = RefCell::new(None);
    let result = dict.locked_for_each(|key, value| {
        f(key, value).map_err(|error| {
            *stopped.borrow_mut() = Some(error);
            PyStopIteration::new_err(())
        })
    });
    match stopped.into_inner() {
        Some(error) => Err(error),
        None => result.map_err(ValError::Fatal),
    }
}

static MAPPING: PyOnceLock<Py<PyType>> = PyOnceLock::new();

fn is_mapping(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    value.is_instance(std_type(
        value.py(),
        &MAPPING,
        "collections.abc",
        "Mapping",
    )?)
}

/// Field access on a model input: an exact `dict` directly, any other `Mapping` through `.get`.
pub(crate) enum Getter<'py> {
    Dict(Bound<'py, PyDict>),
    Mapping(Bound<'py, PyAny>, Bound<'py, PyAny>),
}

impl<'py> Getter<'py> {
    /// `None` when `value` is not a mapping.
    pub(crate) fn new(value: &Bound<'py, PyAny>) -> PyResult<Option<Self>> {
        if let Ok(dict) = value.cast_exact::<PyDict>() {
            return Ok(Some(Self::Dict(dict.clone())));
        }
        if !is_mapping(value)? {
            return Ok(None);
        }
        Ok(Some(Self::Mapping(
            value.clone(),
            errors::missing(value.py())?,
        )))
    }

    pub(crate) fn get(&self, key: &Bound<'py, PyString>) -> PyResult<Option<Bound<'py, PyAny>>> {
        match self {
            Self::Dict(dict) => dict.get_item(key),
            Self::Mapping(mapping, absent) => {
                let item =
                    mapping.call_method1(pyo3::intern!(mapping.py(), "get"), (key, absent))?;
                Ok((!item.is(absent)).then_some(item))
            }
        }
    }
}

/// The [`json_type`] bit of a JSON-shaped value (0 for anything else).
pub(crate) fn json_type_of(value: &Bound<'_, PyAny>) -> PyResult<u8> {
    use json_type::*;
    Ok(if value.is_none() {
        NULL
    } else if value.is_instance_of::<PyBool>() {
        BOOL
    } else if value.is_instance_of::<PyInt>() {
        INT
    } else if value.is_instance_of::<PyFloat>() {
        FLOAT
    } else if value.is_instance_of::<PyString>() {
        STR
    } else if value.is_instance_of::<PyList>() || value.is_instance_of::<PyTuple>() {
        ARRAY
    } else if value.is_instance_of::<PyDict>() || is_mapping(value)? {
        OBJECT
    } else {
        0
    })
}

/// `(type(value), value)`: the key of the enum, literal and tag tables.
pub(crate) fn type_and_value<'py>(value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyTuple>> {
    PyTuple::new(value.py(), [value.get_type().into_any(), value.clone()])
}

/// A smart union: the members `first` picks, then the rest, each in declaration order and in fast
/// mode; the first success wins. A miss is one `expected <label>` line with a note per member.
pub(crate) fn smart<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    members: &[Py<Kind>],
    label: &str,
    ctx: Ctx,
    first: impl Fn(&Kind) -> bool,
    walk: impl Fn(&Bound<'py, PyAny>, &Kind, Ctx) -> VResult<Bound<'py, PyAny>>,
) -> VResult<Bound<'py, PyAny>> {
    let mut notes = Vec::new();
    for pass in [true, false] {
        for member in members {
            let member = member.get();
            if first(member.resolved(py)?) != pass {
                continue;
            }
            match walk(value, member, ctx.fast()) {
                Ok(result) => return Ok(result),
                Err(ValError::Lines(lines)) => {
                    if let Some(line) = lines.into_iter().next() {
                        notes.push((member.label.clone(), line));
                    }
                }
                Err(fatal) => return Err(fatal),
            }
        }
    }
    Err(ValError::Lines(vec![Line {
        loc: Vec::new(),
        message: format!("expected {label}"),
        value: Some(value.clone().unbind()),
        cause: None,
        notes,
    }]))
}
