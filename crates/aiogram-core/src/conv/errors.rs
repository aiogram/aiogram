//! `ConversionError` from Rust: the reason, the offending value and the field path.
//!
//! The messages mirror the ones documented in `aiogram/utils/_converters.py`. A path is built
//! while an error unwinds: each container prepends its segment (`.name`, `[2]`, `['key']`)
//! through `ConversionError._at`.

use pyo3::exceptions::{PyRecursionError, PyTypeError};
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;

/// Nesting depth (models + containers) the walkers recurse to. Deeper input raises
/// `RecursionError` instead of overflowing the native stack.
pub(crate) const MAX_DEPTH: u32 = 512;

static MODULE: PyOnceLock<Py<PyModule>> = PyOnceLock::new();

/// `aiogram.utils._converters`, which defines `ConversionError` and `MISSING`.
pub(crate) fn module(py: Python<'_>) -> PyResult<&Bound<'_, PyModule>> {
    MODULE
        .get_or_try_init(py, || {
            py.import("aiogram.utils._converters").map(Bound::unbind)
        })
        .map(|module| module.bind(py))
}

pub(crate) fn missing(py: Python<'_>) -> PyResult<Bound<'_, PyAny>> {
    module(py)?.getattr("MISSING")
}

fn error_type(py: Python<'_>) -> PyResult<Bound<'_, PyAny>> {
    module(py)?.getattr("ConversionError")
}

/// `ConversionError(reason)` or `ConversionError(reason, value)`.
pub(crate) fn conversion(py: Python<'_>, reason: &str, value: Option<&Bound<'_, PyAny>>) -> PyErr {
    let built = error_type(py).and_then(|cls| match value {
        Some(value) => cls.call1((reason, value)),
        None => cls.call1((reason,)),
    });
    match built {
        Ok(instance) => PyErr::from_value(instance),
        Err(error) => error,
    }
}

/// `_expected(what, value)`: "expected <what> (got <value>)".
pub(crate) fn expected(py: Python<'_>, what: &str, value: &Bound<'_, PyAny>) -> PyErr {
    conversion(py, &format!("expected {what}"), Some(value))
}

/// Prepend a path segment if `error` is a `ConversionError`; the segment is built only then.
pub(crate) fn at(
    py: Python<'_>,
    error: PyErr,
    segment: impl FnOnce() -> PyResult<String>,
) -> PyErr {
    let is_conversion =
        error_type(py).is_ok_and(|cls| error.value(py).is_instance(&cls).unwrap_or(false));
    if is_conversion {
        match segment() {
            Ok(segment) => {
                if let Err(failure) = error.value(py).call_method1("_at", (segment,)) {
                    return failure;
                }
            }
            Err(failure) => return failure,
        }
    }
    error
}

/// Whether `error` is a `ConversionError` (a union member that did not accept the value).
pub(crate) fn is_conversion(py: Python<'_>, error: &PyErr) -> bool {
    error_type(py).is_ok_and(|cls| error.value(py).is_instance(&cls).unwrap_or(false))
}

pub(crate) fn check_depth(depth: u32) -> PyResult<()> {
    if depth > MAX_DEPTH {
        return Err(PyRecursionError::new_err(
            "maximum nesting depth exceeded while converting",
        ));
    }
    Ok(())
}

/// `Converter.to_str` / `from_str` of a type without a flat-string form.
pub(crate) fn no_flat_form(converter: &Bound<'_, PyAny>) -> PyErr {
    match converter.repr() {
        Ok(repr) => PyTypeError::new_err(format!("{repr} has no flat-string form")),
        Err(error) => error,
    }
}
