//! The only "error" this backend has: take the Python path.
//!
//! Every walker returns [`Fallback`] for an input it does not handle as it is (wrong types,
//! missing fields, values outside `i64`, a user converter that raised...). The schema then
//! re-runs the whole input through `ModelConverter._py_*`, so results and `ConversionError`s
//! (message, path, value) are the Python ones by construction.

use pyo3::PyErr;

/// "Take the Python path": the fast path does not apply to this input.
pub(crate) struct Fallback;

/// The result of a fast path.
pub(crate) type Fast<T> = Result<T, Fallback>;

impl From<PyErr> for Fallback {
    fn from(_: PyErr) -> Self {
        Self
    }
}

impl From<jiter::JiterError> for Fallback {
    fn from(_: jiter::JiterError) -> Self {
        Self
    }
}
