//! The only "error" this backend has: take the Python path.
//!
//! Every walker returns [`Fallback::Retry`] for an input it does not handle as it is (wrong
//! types, missing fields, values outside `i64`, a user converter that raised...). The schema
//! then re-runs the whole input through `ModelConverter._py_*`, so results and
//! `ConversionError`s (message, path, value) are the Python ones by construction.
//!
//! A `BaseException` that is not an `Exception` (`KeyboardInterrupt`, `SystemExit`...) is
//! never retried: it is [`Fallback::Raise`]d as it is.

use std::cell::Cell;

use pyo3::exceptions::{PyException, PyValueError};
use pyo3::{PyErr, Python};

/// Nesting depth (models + containers) the walkers recurse to; deeper input falls back, so
/// Python raises its own `RecursionError` instead of the native stack overflowing.
pub(crate) const MAX_DEPTH: u32 = 128;

#[derive(Debug)]
pub(crate) enum Fallback {
    /// The fast path does not apply: run the Python implementation.
    Retry,
    /// Propagate this exception without a retry.
    Raise(PyErr),
}

/// The result of a fast path.
pub(crate) type Fast<T> = Result<T, Fallback>;

impl From<PyErr> for Fallback {
    fn from(error: PyErr) -> Self {
        if Python::attach(|py| error.is_instance_of::<PyException>(py)) {
            Self::Retry
        } else {
            Self::Raise(error)
        }
    }
}

impl From<jiter::JiterError> for Fallback {
    fn from(_: jiter::JiterError) -> Self {
        Self::Retry
    }
}

impl Fallback {
    /// Back into a `PyErr`, for callbacks that must return one; `From<PyErr>` undoes it.
    pub(crate) fn into_pyerr(self) -> PyErr {
        match self {
            Self::Retry => PyValueError::new_err("converter fast path: retry in Python"),
            Self::Raise(error) => error,
        }
    }
}

thread_local! {
    /// Set while a fallback runs, so nested schema calls go straight to Python and user code
    /// (`__post_init__`, user converters, default factories) runs at most twice per input.
    static PYTHON_ONLY: Cell<bool> = const { Cell::new(false) };
}

/// Whether the current thread is inside a fallback.
pub(crate) fn python_only() -> bool {
    PYTHON_ONLY.get()
}

/// Run `python` with nested fast paths disabled on this thread.
pub(crate) fn in_python<T>(python: impl FnOnce() -> T) -> T {
    let previous = PYTHON_ONLY.replace(true);
    let result = python();
    PYTHON_ONLY.set(previous);
    result
}
