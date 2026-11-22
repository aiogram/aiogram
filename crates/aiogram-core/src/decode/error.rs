//! Decode errors: what failed and at which JSON path. They stay Rust values until the caller
//! maps them; the per-update and union isolation is B-14's, the Python-facing classes B-05's.

use std::fmt;

use jiter::{JiterError, JiterErrorType};
use pyo3::PyErr;
use pyo3::exceptions::PyValueError;

use super::seen::Seen;

/// Decoded objects nested deeper than this are an error ([`ErrorKind::Depth`], 13 B7).
pub(crate) const MAX_DEPTH: u16 = 128;

/// One step of a JSON path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum Seg {
    Key(&'static str),
    Index(u32),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum ErrorKind {
    /// Invalid JSON, or a value of the wrong JSON type, in jiter's words (a lone surrogate
    /// in a decoded string is one: Rust `str` cannot hold it)
    Json(Box<str>),
    /// An integer outside the range of the field's type (`"i32"`, `"i64"`)
    Range(&'static str),
    /// A required field is absent or `null`
    Missing,
    /// The input is past the 4 GiB that [`Raw`](super::Raw) offsets address
    TooLarge,
    /// More than [`MAX_DEPTH`] decoded objects nested
    Depth,
    /// Strict mode: an `Unknown…` would have been built
    Strict(Box<Seen>),
}

/// A decode failure. Boxed, so `Result<T, DecodeError>` stays one word wider than `T`.
#[derive(Debug)]
pub(crate) struct DecodeError(Box<Inner>);

#[derive(Debug)]
struct Inner {
    /// innermost segment first: pushed while the error unwinds
    path: Vec<Seg>,
    kind: ErrorKind,
    /// byte offset in the update's buffer
    offset: u32,
}

pub(crate) type DecodeResult<T> = Result<T, DecodeError>;

impl DecodeError {
    #[cold]
    pub(crate) fn new(kind: ErrorKind, offset: u32) -> Self {
        Self(Box::new(Inner {
            path: Vec::new(),
            kind,
            offset,
        }))
    }

    /// `field` of the object starting at `offset` is required and was not set.
    #[cold]
    pub(crate) fn missing(field: &'static str, offset: u32) -> Self {
        Self::new(ErrorKind::Missing, offset).at(Seg::Key(field))
    }

    /// A jiter error at `base` + its index.
    #[cold]
    pub(crate) fn jiter(error: JiterError, base: u32) -> Self {
        let message = match &error.error_type {
            JiterErrorType::JsonError(json) => json.to_string(),
            other @ JiterErrorType::WrongType { .. } => other.to_string(),
        };
        // the cursor keeps `base + len` within u32 (`Cursor::new`), jiter's index within `len`
        let index = u32::try_from(error.index).unwrap_or(u32::MAX);
        Self::new(ErrorKind::Json(message.into()), base.saturating_add(index))
    }

    /// Prefixes the path with `seg` (the error is unwinding out of `seg`).
    #[cold]
    pub(crate) fn at(mut self, seg: Seg) -> Self {
        self.0.path.push(seg);
        self
    }

    /// Moves the offset by `by` bytes (an error of a `getUpdates` element, which counts from
    /// the element, reported against the body).
    pub(crate) fn shifted(mut self, by: u32) -> Self {
        self.0.offset = self.0.offset.saturating_add(by);
        self
    }

    pub(crate) fn kind(&self) -> &ErrorKind {
        &self.0.kind
    }

    /// A depth or strict-mode error: no union absorbs it and no later duplicate key overwrites
    /// it (D107 covers schema mismatches, not the resource guard or the caller's policy).
    pub(crate) fn is_fatal(&self) -> bool {
        matches!(self.0.kind, ErrorKind::Depth | ErrorKind::Strict(_))
    }

    pub(crate) fn offset(&self) -> u32 {
        self.0.offset
    }

    /// The JSON path, outermost first: `message.entities[2].type`; empty for the root.
    pub(crate) fn path(&self) -> String {
        let mut out = String::new();
        for seg in self.0.path.iter().rev() {
            match seg {
                Seg::Key(key) => {
                    if !out.is_empty() {
                        out.push('.');
                    }
                    out.push_str(key);
                }
                Seg::Index(index) => {
                    out.push('[');
                    out.push_str(&index.to_string());
                    out.push(']');
                }
            }
        }
        out
    }
}

impl fmt::Display for DecodeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let path = self.path();
        if !path.is_empty() {
            write!(f, "{path}: ")?;
        }
        match &self.0.kind {
            ErrorKind::Json(message) => f.write_str(message)?,
            ErrorKind::Range(ty) => write!(f, "integer out of range for {ty}")?,
            ErrorKind::Missing => f.write_str("missing required field")?,
            ErrorKind::TooLarge => f.write_str("input larger than 4 GiB")?,
            ErrorKind::Depth => write!(f, "nesting deeper than {MAX_DEPTH} objects")?,
            ErrorKind::Strict(seen) => write!(
                f,
                "{} of {}: {:?} (strict mode)",
                seen.site, seen.entity, seen.value
            )?,
        }
        write!(f, " at byte {}", self.0.offset)
    }
}

/// `from_json` / `from_dict` raise `ValueError` (the per-update error of a batch is B-14's).
impl From<DecodeError> for PyErr {
    fn from(error: DecodeError) -> Self {
        PyValueError::new_err(error.to_string())
    }
}
