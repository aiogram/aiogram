//! Conversion errors, kept in Rust until the API boundary.
//!
//! The walkers return [`ValError`]: either error [`Line`]s (a location, a message and the offending
//! value) or a real Python exception ([`ValError::Fatal`]: `KeyboardInterrupt`, a user converter's
//! `TypeError`, `RecursionError`...). A container pushes its path segment onto every line while the
//! error unwinds, so a failed union member or a failed field costs a few Rust allocations and no
//! Python objects. [`materialize`] builds the one Python `ConversionError` at the boundary.

use std::sync::Mutex;

use pyo3::exceptions::{PyRecursionError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyString, PyTuple};

/// Nesting depth (models + containers) the walkers recurse to. Deeper input raises
/// `RecursionError` instead of overflowing the native stack.
pub(crate) const MAX_DEPTH: u32 = 512;

/// At most this many errors are collected for one conversion (owner, plan-10 Q6).
pub(crate) const MAX_ERRORS: usize = 100;

/// One path segment: a stored key (fields, dict keys) or an array index.
pub(crate) enum Loc {
    Key(Py<PyString>),
    Index(usize),
}

/// One error: `loc` is stored innermost first (segments are pushed while unwinding).
pub(crate) struct Line {
    pub(crate) loc: Vec<Loc>,
    pub(crate) message: String,
    /// The offending value; `None` for errors without one ("field required")
    pub(crate) value: Option<Py<PyAny>>,
    /// The user exception this line came from (`__cause__` of the `ConversionError`)
    pub(crate) cause: Option<PyErr>,
    /// The reasons of union members that did not take the value: (member label, its first
    /// error). Rendered as `add_note` lines at the boundary: `pet: as Cat: lives: expected int,
    /// got 'nine'`.
    pub(crate) notes: Vec<(String, Line)>,
}

pub(crate) enum ValError {
    Lines(Vec<Line>),
    Fatal(PyErr),
}

pub(crate) type VResult<T> = Result<T, ValError>;

impl From<PyErr> for ValError {
    fn from(error: PyErr) -> Self {
        Self::Fatal(error)
    }
}

impl ValError {
    /// One line: `message` about `value`.
    pub(crate) fn new(message: impl Into<String>, value: Option<&Bound<'_, PyAny>>) -> Self {
        Self::Lines(vec![Line {
            loc: Vec::new(),
            message: message.into(),
            value: value.map(|value| value.clone().unbind()),
            cause: None,
            notes: Vec::new(),
        }])
    }

    /// Prepend `segment` to the location of every line.
    #[must_use]
    pub(crate) fn at(mut self, segment: impl Fn() -> Loc) -> Self {
        if let Self::Lines(lines) = &mut self {
            for line in lines {
                line.loc.push(segment());
            }
        }
        self
    }

    #[must_use]
    pub(crate) fn at_key(self, py: Python<'_>, key: &Py<PyString>) -> Self {
        self.at(|| Loc::Key(key.clone_ref(py)))
    }

    #[must_use]
    pub(crate) fn at_index(self, index: usize) -> Self {
        self.at(|| Loc::Index(index))
    }

    /// Append the lines of `other` (collecting mode); a fatal error wins.
    pub(crate) fn extend(self, other: Self) -> Self {
        match (self, other) {
            (Self::Lines(mut lines), Self::Lines(more)) => {
                let room = MAX_ERRORS.saturating_sub(lines.len());
                lines.extend(more.into_iter().take(room));
                Self::Lines(lines)
            }
            (fatal @ Self::Fatal(_), _) | (_, fatal @ Self::Fatal(_)) => fatal,
        }
    }

    /// The number of lines (0 for a fatal error).
    pub(crate) fn len(&self) -> usize {
        match self {
            Self::Lines(lines) => lines.len(),
            Self::Fatal(_) => 0,
        }
    }
}

/// `expected <label>, got <value>` (the value is rendered by `ConversionError.__str__`).
pub(crate) fn expected(label: &str, value: &Bound<'_, PyAny>) -> ValError {
    ValError::new(format!("expected {label}"), Some(value))
}

/// `field required` at `key`.
pub(crate) fn field_required(py: Python<'_>, key: &Py<PyString>) -> ValError {
    ValError::new("field required", None).at_key(py, key)
}

/// Walk state passed down by value: nesting depth, fail-fast mode (union member trials, the flat
/// codec), and `exclude_unset` (top-level model only; walkers clear it for nested values).
#[derive(Clone, Copy)]
pub(crate) struct Ctx {
    pub(crate) depth: u32,
    pub(crate) fast: bool,
    pub(crate) exclude_unset: bool,
}

impl Ctx {
    pub(crate) const fn new(fast: bool) -> Self {
        Self {
            depth: 0,
            fast,
            exclude_unset: false,
        }
    }

    /// One level deeper; `RecursionError` beyond [`MAX_DEPTH`].
    pub(crate) fn deeper(self) -> VResult<Self> {
        if self.depth >= MAX_DEPTH {
            return Err(ValError::Fatal(PyRecursionError::new_err(
                "maximum nesting depth exceeded while converting",
            )));
        }
        Ok(Self {
            depth: self.depth + 1,
            fast: self.fast,
            exclude_unset: false,
        })
    }

    /// Fail-fast copy, for a union member trial.
    pub(crate) const fn fast(self) -> Self {
        Self {
            depth: self.depth,
            fast: true,
            exclude_unset: false,
        }
    }
}

/// The Python classes handed over by `converters_init`.
struct Types {
    error: Py<PyAny>,
    detail: Py<PyAny>,
    missing: Py<PyAny>,
}

static TYPES: Mutex<Option<Types>> = Mutex::new(None);

/// `aiogram._core.conv.converters_init(ConversionError, ErrorDetail, MISSING)`.
#[pyfunction]
pub fn converters_init(
    error: Bound<'_, PyAny>,
    detail: Bound<'_, PyAny>,
    missing: Bound<'_, PyAny>,
) -> PyResult<()> {
    let mut types = TYPES
        .lock()
        .map_err(|_| PyRuntimeError::new_err("converter core state poisoned"))?;
    *types = Some(Types {
        error: error.unbind(),
        detail: detail.unbind(),
        missing: missing.unbind(),
    });
    Ok(())
}

/// `(ConversionError, ErrorDetail, MISSING)`.
fn types(py: Python<'_>) -> PyResult<(Bound<'_, PyAny>, Bound<'_, PyAny>, Bound<'_, PyAny>)> {
    let types = TYPES
        .lock()
        .map_err(|_| PyRuntimeError::new_err("converter core state poisoned"))?;
    let types = types.as_ref().ok_or_else(|| {
        PyRuntimeError::new_err("aiogram.utils._converters has not initialised the converter core")
    })?;
    Ok((
        types.error.bind(py).clone(),
        types.detail.bind(py).clone(),
        types.missing.bind(py).clone(),
    ))
}

/// `MISSING`, the "no value" sentinel of `ErrorDetail.value`.
pub(crate) fn missing(py: Python<'_>) -> PyResult<Bound<'_, PyAny>> {
    Ok(types(py)?.2)
}

/// The Python exception for `error`: a fatal error as is, lines as one `ConversionError(title,
/// errors)` (at most [`MAX_ERRORS`]), with the notes of every line and the first cause.
pub(crate) fn materialize(py: Python<'_>, title: &str, error: ValError) -> PyErr {
    match error {
        ValError::Fatal(error) => error,
        ValError::Lines(lines) => build(py, title, lines).unwrap_or_else(|error| error),
    }
}

fn build(py: Python<'_>, title: &str, lines: Vec<Line>) -> PyResult<PyErr> {
    let (error_type, detail_type, missing) = types(py)?;
    let details = PyList::empty(py);
    let mut notes = Vec::new();
    let mut cause = None;
    for line in lines.into_iter().take(MAX_ERRORS) {
        let loc = PyTuple::new(
            py,
            line.loc.iter().rev().map(|segment| match segment {
                Loc::Key(key) => key.clone_ref(py).into_any(),
                Loc::Index(index) => index
                    .into_pyobject(py)
                    .map_or_else(|_| py.None(), |index| index.into_any().unbind()),
            }),
        )?;
        let value = line
            .value
            .map_or_else(|| missing.clone(), |value| value.into_bound(py));
        details.append(detail_type.call1((loc, &line.message, value))?)?;
        let at = render_loc(py, &line.loc);
        for (label, reason) in &line.notes {
            notes.push(note(py, &at, label, reason)?);
        }
        if cause.is_none() {
            cause = line.cause;
        }
    }
    let instance = error_type.call1((title, details))?;
    for note in notes {
        instance.call_method1(pyo3::intern!(py, "add_note"), (note,))?;
    }
    let error = PyErr::from_value(instance);
    error.set_cause(py, cause);
    Ok(error)
}

/// A user callable's exception as walker error: a `ConversionError` keeps its lines (nested
/// schemas), another `ValueError` becomes one line with the exception as cause, anything else is
/// fatal.
pub(crate) fn from_user(py: Python<'_>, error: PyErr, value: &Bound<'_, PyAny>) -> ValError {
    match lines_of(py, &error) {
        Ok(Some(lines)) => return ValError::Lines(lines),
        Ok(None) => {}
        Err(failure) => return ValError::Fatal(failure),
    }
    if !error.is_instance_of::<PyValueError>(py) {
        return ValError::Fatal(error);
    }
    let message = error
        .value(py)
        .str()
        .map_or_else(|_| String::from("invalid value"), |text| text.to_string());
    ValError::Lines(vec![Line {
        loc: Vec::new(),
        message,
        value: Some(value.clone().unbind()),
        cause: Some(error),
        notes: Vec::new(),
    }])
}

/// The lines of a Python `ConversionError` (its public `errors`), or `None` for another exception.
fn lines_of(py: Python<'_>, error: &PyErr) -> PyResult<Option<Vec<Line>>> {
    let (error_type, _, missing) = types(py)?;
    let instance = error.value(py);
    if !instance.is_instance(&error_type)? {
        return Ok(None);
    }
    let mut lines = Vec::new();
    for detail in instance.getattr(pyo3::intern!(py, "errors"))?.try_iter()? {
        let (loc, message, value): (Bound<'_, PyTuple>, String, Bound<'_, PyAny>) =
            detail?.extract()?;
        let mut segments = Vec::with_capacity(loc.len());
        for segment in loc.iter().rev() {
            segments.push(if let Ok(index) = segment.extract::<usize>() {
                Loc::Index(index)
            } else {
                Loc::Key(segment.str()?.unbind())
            });
        }
        lines.push(Line {
            loc: segments,
            message,
            value: (!value.is(&missing)).then(|| value.unbind()),
            cause: None,
            notes: Vec::new(),
        });
    }
    // a ConversionError without details: the ValueError path (its text, as the cause)
    Ok((!lines.is_empty()).then_some(lines))
}

/// `<loc>: as <member>: <reason loc>: <message>, got <value repr>`.
fn note(py: Python<'_>, at: &str, label: &str, reason: &Line) -> PyResult<String> {
    let mut text = String::new();
    if !at.is_empty() {
        text.push_str(at);
        text.push_str(": ");
    }
    text.push_str("as ");
    text.push_str(label);
    text.push_str(": ");
    let inner = render_loc(py, &reason.loc);
    if !inner.is_empty() {
        text.push_str(&inner);
        text.push_str(": ");
    }
    text.push_str(&reason.message);
    if let Some(value) = &reason.value {
        text.push_str(", got ");
        text.push_str(&short_repr(&value.bind(py).repr()?.to_string()));
    }
    Ok(text)
}

/// A repr cut to 80 characters, as `ConversionError.__str__` cuts values (`reprlib`).
fn short_repr(text: &str) -> String {
    const LIMIT: usize = 80;
    if text.chars().count() <= LIMIT {
        return text.to_owned();
    }
    let mut short: String = text.chars().take(LIMIT - 3).collect();
    short.push_str("...");
    short
}

/// The path of a line as `ConversionError` renders it (`address.zip`, `tags[2]`), for notes.
pub(crate) fn render_loc(py: Python<'_>, loc: &[Loc]) -> String {
    let mut text = String::new();
    for segment in loc.iter().rev() {
        match segment {
            Loc::Index(index) => text.push_str(&format!("[{index}]")),
            Loc::Key(key) => {
                if !text.is_empty() {
                    text.push('.');
                }
                text.push_str(&key.bind(py).to_string_lossy());
            }
        }
    }
    text
}
