//! The scalar kinds: Python glue shared by the dict load, the bytes load, the dump, the write and
//! the flat codec. Text goes through `native::*` first and falls back to the stdlib constructor.

use std::io::Write as _;

use pyo3::exceptions::{PyArithmeticError, PyOSError, PyRuntimeError, PyTypeError, PyValueError};
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{
    PyBool, PyBytes, PyDate, PyDateAccess, PyDateTime, PyDelta, PyDeltaAccess, PyFloat, PyInt,
    PyString, PyTime, PyTimeAccess, PyType, PyTzInfo, PyTzInfoAccess,
};

use super::errors::{VResult, ValError, expected, from_user};
use super::ir::{
    DATE, DATETIME, DECIMAL, Data, Enumeration, Epoch, Kind, Literal, TIME, TIMEDELTA, Text, UUID,
    std_type,
};
use super::native::{base64, iso, number, uuid};
use super::walk::type_and_value;

static OBJECT_NEW: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static SAFE_UUID: PyOnceLock<Py<PyType>> = PyOnceLock::new();

/// `object.__setattr__(obj, name, value)`: works with slots and `__dict__`, and bypasses a frozen
/// class's own `__setattr__`.
pub(crate) fn set_attr(
    obj: &Bound<'_, PyAny>,
    name: &Bound<'_, PyString>,
    value: &Bound<'_, PyAny>,
) -> PyResult<()> {
    // SAFETY: the three pointers are live objects borrowed for the duration of the call, and the
    // attached `Python` token of `obj` proves the thread is attached to the interpreter.
    let status =
        unsafe { ffi::PyObject_GenericSetAttr(obj.as_ptr(), name.as_ptr(), value.as_ptr()) };
    if status == 0 {
        Ok(())
    } else {
        Err(PyErr::fetch(obj.py()))
    }
}

/// `object.__new__(tp)`.
pub(crate) fn new_instance<'py>(tp: &Bound<'py, PyType>) -> PyResult<Bound<'py, PyAny>> {
    let py = tp.py();
    OBJECT_NEW
        .get_or_try_init(py, || {
            py.get_type::<PyAny>().getattr("__new__").map(Bound::unbind)
        })?
        .bind(py)
        .call1((tp,))
}

/// A stdlib constructor's `ValueError` / `ArithmeticError` (and `OSError` for timestamps) is the
/// kind's "expected" line; anything else is fatal.
fn coerce(py: Python<'_>, error: PyErr, label: &str, value: &Bound<'_, PyAny>) -> ValError {
    if error.is_instance_of::<PyValueError>(py)
        || error.is_instance_of::<PyArithmeticError>(py)
        || error.is_instance_of::<PyOSError>(py)
    {
        expected(label, value)
    } else {
        ValError::Fatal(error)
    }
}

/// Text handed to a text kind: borrowed from the JSON document, or a Python `str`.
#[derive(Clone, Copy)]
pub(crate) enum TextIn<'a, 'py> {
    Str(&'a str),
    Py(&'a Bound<'py, PyString>),
}

impl<'a, 'py> TextIn<'a, 'py> {
    /// The UTF-8 text; `None` for a `str` with lone surrogates.
    fn text(self) -> Option<&'a str> {
        match self {
            Self::Str(text) => Some(text),
            Self::Py(text) => text.to_str().ok(),
        }
    }

    fn object(self, py: Python<'py>) -> Bound<'py, PyString> {
        match self {
            Self::Str(text) => PyString::new(py, text),
            Self::Py(text) => text.clone(),
        }
    }
}

// ---- int / float / bool ----------------------------------------------------------------

/// `int`: an exact `int` as is, an `int` subclass (not `bool`) through `int()`.
pub(crate) fn int<'py>(value: &Bound<'py, PyAny>, label: &str) -> VResult<Bound<'py, PyAny>> {
    if value.is_exact_instance_of::<PyInt>() {
        return Ok(value.clone());
    }
    if value.is_instance_of::<PyInt>() && !value.is_instance_of::<PyBool>() {
        return Ok(value.py().get_type::<PyInt>().call1((value,))?);
    }
    Err(expected(label, value))
}

/// `float`: an exact `float` as is, a `float` subclass or an `int` (not `bool`) through
/// `float()`; an `int` too large for a float is "expected float".
pub(crate) fn float<'py>(value: &Bound<'py, PyAny>, label: &str) -> VResult<Bound<'py, PyAny>> {
    if value.is_exact_instance_of::<PyFloat>() {
        return Ok(value.clone());
    }
    if (value.is_instance_of::<PyFloat>() || value.is_instance_of::<PyInt>())
        && !value.is_instance_of::<PyBool>()
    {
        let py = value.py();
        return py
            .get_type::<PyFloat>()
            .call1((value,))
            .map_err(|e| coerce(py, e, label, value));
    }
    Err(expected(label, value))
}

/// `float` as an `f64` (the write and flat paths).
pub(crate) fn float_value(value: &Bound<'_, PyAny>, label: &str) -> VResult<f64> {
    if let Ok(float) = value.cast_exact::<PyFloat>() {
        return Ok(float.value());
    }
    Ok(float(value, label)?.extract::<f64>()?)
}

pub(crate) fn boolean<'py>(value: &Bound<'py, PyAny>, label: &str) -> VResult<Bound<'py, PyAny>> {
    if value.is_instance_of::<PyBool>() {
        Ok(value.clone())
    } else {
        Err(expected(label, value))
    }
}

pub(crate) fn py_bool(py: Python<'_>, value: bool) -> Bound<'_, PyAny> {
    PyBool::new(py, value).to_owned().into_any()
}

/// Append the decimal text of an `int` (any size; subclasses as `int(value)`).
pub(crate) fn write_int(value: &Bound<'_, PyAny>, out: &mut Vec<u8>) -> PyResult<()> {
    // exact ints only: a subclass goes through `int(value)`, as the dict dump does
    if value.is_exact_instance_of::<PyInt>()
        && let Ok(small) = value.extract::<i64>()
    {
        let _ = write!(out, "{small}");
        return Ok(());
    }
    let text = if value.is_exact_instance_of::<PyInt>() {
        value.str()?
    } else {
        value.py().get_type::<PyInt>().call1((value,))?.str()?
    };
    out.extend_from_slice(text.to_str()?.as_bytes());
    Ok(())
}

// ---- text kinds: UUID, datetime, date, time, Decimal text, bytes ------------------------------

/// A text kind (`str_`, `uuid`, ISO `datetime`, `date`, `time`, text `decimal`, `bytes_`) from
/// its text.
pub(crate) fn load_text<'py>(
    py: Python<'py>,
    kind: &Kind,
    text: TextIn<'_, 'py>,
) -> VResult<Bound<'py, PyAny>> {
    let label = kind.label.as_str();
    match &kind.data {
        Data::Str => Ok(text.object(py).into_any()),
        Data::Uuid { .. } => load_uuid(py, text, label),
        Data::Datetime { .. } => {
            if let Some(parts) = text.text().and_then(iso::parse_datetime)
                && let Ok(value) = datetime(py, &parts.0, &parts.1)
            {
                return Ok(value.into_any());
            }
            from_iso(py, &DATETIME, "datetime", text, label)
        }
        Data::Date => {
            if let Some(date) = text.text().and_then(iso::parse_date)
                && let Ok(value) = PyDate::new(py, date.year, date.month, date.day)
            {
                return Ok(value.into_any());
            }
            from_iso(py, &DATE, "date", text, label)
        }
        Data::Time { .. } => {
            if let Some(time) = text.text().and_then(iso::parse_time)
                && let Ok(value) = make_time(py, &time)
            {
                return Ok(value.into_any());
            }
            from_iso(py, &TIME, "time", text, label)
        }
        Data::Decimal { .. } => decimal(py, &text.object(py).into_any(), label),
        Data::Bytes => match text.text().and_then(|text| base64::decode(text, false)) {
            Some(data) => Ok(PyBytes::new(py, &data).into_any()),
            None => Err(expected(label, &text.object(py).into_any())),
        },
        _ => Err(ValError::Fatal(PyRuntimeError::new_err(format!(
            "{label} is not a text kind"
        )))),
    }
}

/// Whether [`load_text`] takes this kind.
pub(crate) fn is_text_kind(kind: &Kind) -> bool {
    matches!(
        kind.data,
        Data::Str
            | Data::Uuid { .. }
            | Data::Datetime { epoch: None, .. }
            | Data::Date
            | Data::Time { .. }
            | Data::Decimal { number: false }
            | Data::Bytes
    )
}

fn from_iso<'py>(
    py: Python<'py>,
    cell: &'static PyOnceLock<Py<PyType>>,
    name: &str,
    text: TextIn<'_, 'py>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let text = text.object(py);
    std_type(py, cell, "datetime", name)?
        .call_method1(pyo3::intern!(py, "fromisoformat"), (&text,))
        .map_err(|e| coerce(py, e, label, &text))
}

fn load_uuid<'py>(
    py: Python<'py>,
    text: TextIn<'_, 'py>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    if let Some(raw) = text.text() {
        if let Some(value) = uuid::parse(raw) {
            return Ok(make_uuid(py, value)?);
        }
        // `UUID(text)` drops `urn:`, `uuid:`, the braces around and every hyphen, then needs
        // exactly 32 characters: anything else is a miss without calling Python
        let core = raw.replace("urn:", "").replace("uuid:", "");
        let core = core.trim_matches(['{', '}']);
        if core.chars().filter(|c| *c != '-').count() != 32 {
            return Err(expected(label, &text.object(py).into_any()));
        }
    }
    let text = text.object(py);
    std_type(py, &UUID, "uuid", "UUID")?
        .call1((&text,))
        .map_err(|e| coerce(py, e, label, &text))
}

/// `object.__new__(UUID)` with `int` and `is_safe = SafeUUID.unknown` set directly.
pub(crate) fn make_uuid(py: Python<'_>, value: u128) -> PyResult<Bound<'_, PyAny>> {
    let instance = new_instance(std_type(py, &UUID, "uuid", "UUID")?)?;
    set_attr(
        &instance,
        pyo3::intern!(py, "int"),
        &value.into_pyobject(py)?.into_any(),
    )?;
    let unknown =
        std_type(py, &SAFE_UUID, "uuid", "SafeUUID")?.getattr(pyo3::intern!(py, "unknown"))?;
    set_attr(&instance, pyo3::intern!(py, "is_safe"), &unknown)?;
    Ok(instance)
}

/// The `tzinfo` of a parsed offset: `timezone.utc` for 0, else `timezone(timedelta(...))`.
fn tzinfo(py: Python<'_>, offset: Option<i64>) -> PyResult<Option<Bound<'_, PyTzInfo>>> {
    match offset {
        None => Ok(None),
        Some(0) => Ok(Some(PyTzInfo::utc(py)?.to_owned())),
        Some(micros) => {
            let seconds = i32::try_from(micros.div_euclid(1_000_000))
                .map_err(|_| PyValueError::new_err("offset out of range"))?;
            let micros = i32::try_from(micros.rem_euclid(1_000_000)).unwrap_or(0);
            let delta = PyDelta::new(py, 0, seconds, micros, true)?;
            Ok(Some(PyTzInfo::fixed_offset(py, delta)?))
        }
    }
}

fn datetime<'py>(
    py: Python<'py>,
    date: &iso::Date,
    time: &iso::Time,
) -> PyResult<Bound<'py, PyDateTime>> {
    let tz = tzinfo(py, time.offset)?;
    PyDateTime::new(
        py,
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
        time.second,
        time.microsecond,
        tz.as_ref(),
    )
}

fn make_time<'py>(py: Python<'py>, time: &iso::Time) -> PyResult<Bound<'py, PyTime>> {
    let tz = tzinfo(py, time.offset)?;
    PyTime::new(
        py,
        time.hour,
        time.minute,
        time.second,
        time.microsecond,
        tz.as_ref(),
    )
}

/// `utcoffset()` in microseconds, or `None` when naive.
fn offset(value: &Bound<'_, PyAny>, tz: Option<Bound<'_, PyTzInfo>>) -> PyResult<Option<i64>> {
    let Some(tz) = tz else { return Ok(None) };
    let py = value.py();
    if tz.is(&*PyTzInfo::utc(py)?) {
        return Ok(Some(0));
    }
    let delta = value.call_method0(pyo3::intern!(py, "utcoffset"))?;
    if delta.is_none() {
        return Ok(None);
    }
    let delta = delta.cast_into::<PyDelta>()?;
    Ok(Some(
        (i64::from(delta.get_days()) * 86_400 + i64::from(delta.get_seconds())) * 1_000_000
            + i64::from(delta.get_microseconds()),
    ))
}

fn date_parts(value: &impl PyDateAccess) -> iso::Date {
    iso::Date {
        year: value.get_year(),
        month: value.get_month(),
        day: value.get_day(),
    }
}

fn time_parts(value: &impl PyTimeAccess, offset: Option<i64>) -> iso::Time {
    iso::Time {
        hour: value.get_hour(),
        minute: value.get_minute(),
        second: value.get_second(),
        microsecond: value.get_microsecond(),
        offset,
    }
}

/// Append the text of a text kind's value (dump / write); "expected" for a wrong type.
pub(crate) fn dump_text(
    py: Python<'_>,
    value: &Bound<'_, PyAny>,
    kind: &Kind,
    out: &mut String,
) -> VResult<()> {
    let label = kind.label.as_str();
    match &kind.data {
        Data::Uuid { hex } => {
            if !value.is_instance(std_type(py, &UUID, "uuid", "UUID")?)? {
                return Err(expected(label, value));
            }
            uuid::write(uuid_int(value)?, *hex, out);
        }
        Data::Datetime { timespec, sep, .. } => {
            let dt = value
                .cast::<PyDateTime>()
                .map_err(|_| expected(label, value))?;
            let time = time_parts(dt, offset(value, dt.get_tzinfo())?);
            iso::write_datetime(&date_parts(dt), &time, *sep, *timespec, out);
        }
        Data::Date => {
            let date = value.cast::<PyDate>().map_err(|_| expected(label, value))?;
            if value.is_instance_of::<PyDateTime>() {
                return Err(expected(label, value));
            }
            iso::write_date(&date_parts(date), out);
        }
        Data::Time { timespec } => {
            let time = value.cast::<PyTime>().map_err(|_| expected(label, value))?;
            iso::write_time(
                &time_parts(time, offset(value, time.get_tzinfo())?),
                *timespec,
                out,
            );
        }
        Data::Decimal { .. } => {
            if !value.is_instance(std_type(py, &DECIMAL, "decimal", "Decimal")?)? {
                return Err(expected(label, value));
            }
            out.push_str(value.str()?.to_str()?);
        }
        Data::Bytes => {
            let bytes = value
                .cast::<PyBytes>()
                .map_err(|_| expected(label, value))?;
            out.push_str(&base64::encode(bytes.as_bytes(), false));
        }
        _ => {
            return Err(ValError::Fatal(PyRuntimeError::new_err(format!(
                "{label} has no text form"
            ))));
        }
    }
    Ok(())
}

/// The flat text of a `datetime` / `date` / `time`: ISO 8601 basic (no `-` / `:`, so never a
/// callback-data separator); `timespec` applies, `sep` does not (basic always uses `T`).
pub(crate) fn dump_basic(value: &Bound<'_, PyAny>, kind: &Kind, out: &mut String) -> VResult<()> {
    let label = kind.label.as_str();
    match &kind.data {
        Data::Datetime { timespec, .. } => {
            let dt = value
                .cast::<PyDateTime>()
                .map_err(|_| expected(label, value))?;
            let time = time_parts(dt, offset(value, dt.get_tzinfo())?);
            iso::write_datetime_basic(&date_parts(dt), &time, *timespec, out);
        }
        Data::Date => {
            let date = value.cast::<PyDate>().map_err(|_| expected(label, value))?;
            if value.is_instance_of::<PyDateTime>() {
                return Err(expected(label, value));
            }
            iso::write_date_basic(&date_parts(date), out);
        }
        Data::Time { timespec } => {
            let time = value.cast::<PyTime>().map_err(|_| expected(label, value))?;
            iso::write_time_basic(
                &time_parts(time, offset(value, time.get_tzinfo())?),
                *timespec,
                out,
            );
        }
        _ => {
            return Err(ValError::Fatal(PyRuntimeError::new_err(format!(
                "{label} has no ISO form"
            ))));
        }
    }
    Ok(())
}

/// `uuid.int`.
pub(crate) fn uuid_int(value: &Bound<'_, PyAny>) -> PyResult<u128> {
    value.getattr(pyo3::intern!(value.py(), "int"))?.extract()
}

// ---- numbers: epoch datetime, timedelta, Decimal number ---------------------------------------

/// A number produced by a dump: written natively, or handed out as a Python object.
pub(crate) enum Num<'py> {
    Int(i64),
    Float(f64),
    Obj(Bound<'py, PyAny>),
}

impl<'py> Num<'py> {
    pub(crate) fn object(self, py: Python<'py>) -> Bound<'py, PyAny> {
        match self {
            Self::Int(value) => PyInt::new(py, value).into_any(),
            Self::Float(value) => PyFloat::new(py, value).into_any(),
            Self::Obj(value) => value,
        }
    }

    pub(crate) fn write(&self, out: &mut Vec<u8>) -> PyResult<()> {
        match self {
            Self::Int(value) => {
                let _ = write!(out, "{value}");
            }
            Self::Float(value) => number::write_float(*value, out),
            Self::Obj(value) => number::write_float(value.extract::<f64>()?, out),
        }
        Ok(())
    }

    /// `total / unit`: an `int` when exact, else a `float`.
    fn ratio(total: i64, unit: i64) -> Self {
        if total % unit == 0 {
            Self::Int(total / unit)
        } else {
            #[allow(clippy::cast_precision_loss)] // the float form is lossy by definition
            Self::Float(total as f64 / unit as f64)
        }
    }
}

const fn epoch_unit(epoch: Epoch) -> i64 {
    match epoch {
        Epoch::Seconds => 1_000_000,
        Epoch::Milliseconds => 1_000,
    }
}

fn is_number(value: &Bound<'_, PyAny>) -> bool {
    (value.is_instance_of::<PyInt>() || value.is_instance_of::<PyFloat>())
        && !value.is_instance_of::<PyBool>()
}

/// `datetime.fromtimestamp(x, timezone.utc)` of an `int` / `float` (ms: `x / 1000`), computed
/// here: whole seconds exactly, a fraction rounded half-even to microseconds as CPython does.
pub(crate) fn load_epoch<'py>(
    value: &Bound<'py, PyAny>,
    epoch: Epoch,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let py = value.py();
    if !is_number(value) {
        return Err(expected(label, value));
    }
    let (seconds, micros) = if value.is_instance_of::<PyInt>() && epoch == Epoch::Seconds {
        (
            value.extract::<i64>().map_err(|_| expected(label, value))?,
            0,
        )
    } else {
        #[allow(clippy::cast_precision_loss)] // `x / 1000` is a float division in Python too
        let stamp = match value.extract::<i64>() {
            Ok(int) => int as f64,
            Err(_) => value
                .extract::<f64>()
                .map_err(|e| coerce(py, e, label, value))?,
        };
        let stamp = if epoch == Epoch::Milliseconds {
            stamp / 1000.0
        } else {
            stamp
        };
        if !stamp.is_finite() || stamp.abs() > 1e15 {
            return Err(expected(label, value));
        }
        let whole = stamp.trunc();
        let mut micros = ((stamp - whole) * 1e6).round_ties_even();
        let mut whole = whole;
        if micros >= 1e6 {
            whole += 1.0;
            micros -= 1e6;
        } else if micros < 0.0 {
            whole -= 1.0;
            micros += 1e6;
        }
        #[allow(clippy::cast_possible_truncation)] // both are in range (checked above)
        (whole as i64, micros as u32)
    };
    let days = seconds.div_euclid(86_400);
    let rest = seconds.rem_euclid(86_400);
    // the datetime range: years 1..=9999
    if !(-719_162..=2_932_896).contains(&days) {
        return Err(expected(label, value));
    }
    let date = iso::civil_from_days(days);
    #[allow(clippy::cast_possible_truncation, clippy::cast_sign_loss)] // 0 <= rest < 86400
    let time = iso::Time {
        hour: (rest / 3600) as u8,
        minute: (rest / 60 % 60) as u8,
        second: (rest % 60) as u8,
        microsecond: micros,
        offset: Some(0),
    };
    Ok(datetime(py, &date, &time)
        .map_err(|e| coerce(py, e, label, value))?
        .into_any())
}

/// An epoch `datetime` as a number: computed here when aware, through `timestamp()` when naive.
pub(crate) fn dump_epoch<'py>(
    value: &Bound<'py, PyAny>,
    epoch: Epoch,
    label: &str,
) -> VResult<Num<'py>> {
    let py = value.py();
    let dt = value
        .cast::<PyDateTime>()
        .map_err(|_| expected(label, value))?;
    let micros = i64::from(dt.get_microsecond());
    let total = if let Some(offset) = offset(value, dt.get_tzinfo())? {
        let days = iso::days_from_civil(dt.get_year(), dt.get_month(), dt.get_day());
        let seconds = days * 86_400
            + i64::from(dt.get_hour()) * 3600
            + i64::from(dt.get_minute()) * 60
            + i64::from(dt.get_second());
        seconds * 1_000_000 + micros - offset
    } else {
        let stamp: f64 = value
            .call_method0(pyo3::intern!(py, "timestamp"))
            .and_then(|stamp| stamp.extract())
            .map_err(|e| coerce(py, e, label, value))?;
        #[allow(clippy::cast_possible_truncation, clippy::cast_precision_loss)]
        // whole seconds of a datetime
        let whole = (stamp - micros as f64 / 1e6).round() as i64;
        whole * 1_000_000 + micros
    };
    let unit = epoch_unit(epoch);
    if total % unit != 0 && total.unsigned_abs() >= (1 << 53) {
        // beyond 2**53 microseconds a float division rounds twice: Python's int / int does not
        let quotient =
            PyInt::new(py, total).call_method1(pyo3::intern!(py, "__truediv__"), (unit,))?;
        return Ok(Num::Obj(quotient.into_any()));
    }
    Ok(Num::ratio(total, unit))
}

/// `timedelta(seconds=x)` of an `int` / `float` (not `bool`).
pub(crate) fn load_timedelta<'py>(
    value: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let py = value.py();
    if !is_number(value) {
        return Err(expected(label, value));
    }
    if value.is_instance_of::<PyInt>() {
        let seconds = value.extract::<i64>().map_err(|_| expected(label, value))?;
        let days = i32::try_from(seconds.div_euclid(86_400)).map_err(|_| expected(label, value))?;
        let rest = i32::try_from(seconds.rem_euclid(86_400)).unwrap_or(0);
        return PyDelta::new(py, days, rest, 0, true)
            .map(Bound::into_any)
            .map_err(|e| coerce(py, e, label, value));
    }
    std_type(py, &TIMEDELTA, "datetime", "timedelta")?
        .call1((0, value))
        .map_err(|e| coerce(py, e, label, value))
}

/// `total_seconds()`: an `int` without microseconds, else a `float`.
pub(crate) fn dump_timedelta<'py>(value: &Bound<'py, PyAny>, label: &str) -> VResult<Num<'py>> {
    let delta = value
        .cast::<PyDelta>()
        .map_err(|_| expected(label, value))?;
    let seconds = i64::from(delta.get_days()) * 86_400 + i64::from(delta.get_seconds());
    let micros = i64::from(delta.get_microseconds());
    if micros == 0 {
        return Ok(Num::Int(seconds));
    }
    // exact in a float below 2**53 microseconds; beyond, Python's correctly rounded division
    if let Some(total) = seconds
        .checked_mul(1_000_000)
        .and_then(|total| total.checked_add(micros))
        && total.unsigned_abs() < (1 << 53)
    {
        return Ok(Num::ratio(total, 1_000_000));
    }
    Ok(Num::Obj(value.call_method0(pyo3::intern!(
        value.py(),
        "total_seconds"
    ))?))
}

/// `Decimal(text)`.
pub(crate) fn decimal<'py>(
    py: Python<'py>,
    text: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    std_type(py, &DECIMAL, "decimal", "Decimal")?
        .call1((text,))
        .map_err(|e| coerce(py, e, label, text))
}

/// The dict load of a `Decimal` number: `Decimal(str(x))` of an `int` / `float`.
pub(crate) fn load_decimal_number<'py>(
    value: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    if !is_number(value) {
        return Err(expected(label, value));
    }
    decimal_number(value.py(), &value.str()?.into_any(), label).map_err(|error| match error {
        ValError::Lines(_) => expected(label, value),
        fatal @ ValError::Fatal(_) => fatal,
    })
}

/// `Decimal(text)` of a JSON number, which must be finite (`DecimalAsNumber` dumps only
/// finite values, so NaN / Infinity would not round-trip).
pub(crate) fn decimal_number<'py>(
    py: Python<'py>,
    text: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let value = decimal(py, text, label)?;
    finite_decimal(&value, label).map_err(|_| expected(label, text))?;
    Ok(value)
}

/// A finite `Decimal`, or "expected".
pub(crate) fn finite_decimal(value: &Bound<'_, PyAny>, label: &str) -> VResult<()> {
    let py = value.py();
    if value.is_instance(std_type(py, &DECIMAL, "decimal", "Decimal")?)?
        && value
            .call_method0(pyo3::intern!(py, "is_finite"))?
            .is_truthy()?
    {
        Ok(())
    } else {
        Err(expected(label, value))
    }
}

// ---- user text, enums, literals --------------------------------------------------------------

/// `Text.parse(text)`: an `ArithmeticError` is "expected", other errors go through `from_user`.
pub(crate) fn parse_text<'py>(
    text: &Text,
    value: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let py = value.py();
    if !value.is_instance_of::<PyString>() {
        return Err(expected(label, value));
    }
    text.parse.bind(py).call1((value,)).map_err(|error| {
        if error.is_instance_of::<PyArithmeticError>(py) {
            expected(label, value)
        } else {
            from_user(py, error, value)
        }
    })
}

/// `Text.format(value)` of an instance of the kind's type; the result must be a `str`.
pub(crate) fn format_text<'py>(
    text: &Text,
    value: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyString>> {
    let py = value.py();
    if !value.is_instance(text.tp.bind(py))? {
        return Err(expected(label, value));
    }
    let result = text
        .format
        .bind(py)
        .call1((value,))
        .map_err(|e| from_user(py, e, value))?;
    result.cast_into::<PyString>().map_err(|error| {
        ValError::Fatal(PyTypeError::new_err(format!(
            "{label} format returned {}, not str",
            error
                .into_inner()
                .get_type()
                .name()
                .map_or_else(|_| String::from("?"), |name| name.to_string())
        )))
    })
}

/// `tp._missing_(value)` of a tolerant enum: only a member counts, a `ValueError` is a miss.
pub(crate) fn enum_missing<'py>(
    enumeration: &Enumeration,
    value: &Bound<'py, PyAny>,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    if !enumeration.missing {
        return Ok(None);
    }
    let py = value.py();
    let tp = enumeration.tp.bind(py);
    match tp.call_method1(pyo3::intern!(py, "_missing_"), (value,)) {
        Ok(member) if member.is_instance(tp)? => Ok(Some(member)),
        Ok(_) => Ok(None),
        Err(error) if error.is_instance_of::<PyValueError>(py) => Ok(None),
        Err(error) => Err(error),
    }
}

/// The JSON load of an enum: by `(type(v), v)`, or by name.
pub(crate) fn load_enum<'py>(
    enumeration: &Enumeration,
    value: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let py = value.py();
    let json = enumeration.json.bind(py);
    let found = if enumeration.by_name {
        if !value.is_instance_of::<PyString>() {
            return Err(expected(label, value));
        }
        json.get_item(value)?
    } else {
        // an unhashable value is a miss
        json.get_item(type_and_value(value)?).ok().flatten()
    };
    if let Some(member) = found {
        return Ok(member);
    }
    enum_missing(enumeration, value)?.ok_or_else(|| expected(label, value))
}

/// A member's `.value` (by value) or `.name` (by name).
pub(crate) fn dump_enum<'py>(
    enumeration: &Enumeration,
    value: &Bound<'py, PyAny>,
    label: &str,
) -> VResult<Bound<'py, PyAny>> {
    let py = value.py();
    if !value.is_instance(enumeration.tp.bind(py))? {
        return Err(expected(label, value));
    }
    let attribute = if enumeration.by_name {
        pyo3::intern!(py, "name")
    } else {
        pyo3::intern!(py, "value")
    };
    Ok(value.getattr(attribute)?)
}

/// `(type(v), v) in literal.json`; an unhashable value is a miss.
pub(crate) fn check_literal(
    literal: &Literal,
    value: &Bound<'_, PyAny>,
    label: &str,
) -> VResult<()> {
    let py = value.py();
    let pair = type_and_value(value)?;
    if literal.json.bind(py).contains(pair).unwrap_or(false) {
        Ok(())
    } else {
        Err(expected(label, value))
    }
}
