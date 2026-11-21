//! The flat-string codec: callback-data parts (`to_str` / `from_str`).

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyString};

use super::dump::check_text;
use super::errors::{self, expected, no_flat_form};
use super::kind::{Data, Kind};
use super::load::{boolean, float, int, literal_value, parse_text, string};

static BOOL_TEXT: PyOnceLock<Py<PyDict>> = PyOnceLock::new();

pub(crate) fn from_str<'py>(
    py: Python<'py>,
    part: &Bound<'py, PyAny>,
    kind: &Kind,
) -> PyResult<Bound<'py, PyAny>> {
    let converter = kind.converter.bind(py);
    match &kind.data {
        Data::Str => Ok(part.clone()),
        Data::Int => {
            if let Some(int) = exact_str(part).and_then(parse_int) {
                return Ok(PyInt::new(py, int).into_any());
            }
            convert_text(py, py.get_type::<PyInt>().as_any(), part, "an integer")
        }
        Data::Float => {
            if let Some(float) = exact_str(part).and_then(parse_float) {
                return Ok(PyFloat::new(py, float).into_any());
            }
            convert_text(py, py.get_type::<PyFloat>().as_any(), part, "a number")
        }
        Data::Bool => match exact_str(part) {
            Some("1") => Ok(PyBool::new(py, true).to_owned().into_any()),
            Some("0") => Ok(PyBool::new(py, false).to_owned().into_any()),
            _ => {
                // the lax set ("true", "Off", ...) is `_BOOL_TEXT[value.lower()]`
                let lowered = part.call_method0(pyo3::intern!(py, "lower"))?;
                let table = BOOL_TEXT.get_or_try_init(py, || -> PyResult<_> {
                    Ok(errors::module(py)?
                        .getattr("_BOOL_TEXT")?
                        .cast_into::<PyDict>()?
                        .unbind())
                })?;
                table
                    .bind(py)
                    .get_item(lowered)?
                    .ok_or_else(|| expected(py, "a boolean", part))
            }
        },
        Data::Text(text) if text.flat => parse_text(py, text, part),
        Data::Enum(enumeration) => match &enumeration.by_text {
            Some(by_text) => by_text
                .bind(py)
                .get_item(part)?
                .ok_or_else(|| expected(py, &format!("a {} value", enumeration.name), part)),
            None => Err(no_flat_form(converter)),
        },
        Data::Literal(literal) => match &literal.text {
            Some(text) => text
                .bind(py)
                .get_item(part)?
                .ok_or_else(|| expected(py, &literal.label, part)),
            None => Err(no_flat_form(converter)),
        },
        Data::Optional { inner, flat: true } => {
            if part.eq("")? {
                Ok(py.None().into_bound(py))
            } else {
                from_str(py, part, inner)
            }
        }
        Data::Python => converter.call_method1(pyo3::intern!(py, "from_str"), (part,)),
        _ => Err(no_flat_form(converter)),
    }
}

pub(crate) fn to_str<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
) -> PyResult<Bound<'py, PyAny>> {
    let converter = kind.converter.bind(py);
    match &kind.data {
        Data::Str => string(py, value),
        Data::Int => Ok(int(py, value)?.str()?.into_any()),
        Data::Float => Ok(float(py, value)?.str()?.into_any()),
        Data::Bool => Ok(bool_text(py, boolean(py, value)?.is_truthy()?)),
        Data::Text(text) if text.flat => {
            text.to_flat.bind(py).call1((check_text(py, text, value)?,))
        }
        Data::Enum(enumeration) if enumeration.by_text.is_some() => {
            if !value.is_instance(enumeration.tp.bind(py))? {
                return Err(expected(
                    py,
                    &format!("a {} member", enumeration.name),
                    value,
                ));
            }
            Ok(value.getattr(pyo3::intern!(py, "value"))?.str()?.into_any())
        }
        Data::Literal(literal) if literal.text.is_some() => {
            // `_literal_text`: None -> "", bool -> "1" / "0", else str(value)
            let value = literal_value(py, literal, value)?;
            if value.is_none() {
                Ok(PyString::new(py, "").into_any())
            } else if value.is_instance_of::<PyBool>() {
                Ok(bool_text(py, value.is_truthy()?))
            } else {
                Ok(value.str()?.into_any())
            }
        }
        Data::Optional { inner, flat: true } => {
            if value.is_none() {
                Ok(PyString::new(py, "").into_any())
            } else {
                to_str(py, value, inner)
            }
        }
        Data::Python => converter.call_method1(pyo3::intern!(py, "to_str"), (value,)),
        _ => Err(no_flat_form(converter)),
    }
}

fn bool_text(py: Python<'_>, value: bool) -> Bound<'_, PyAny> {
    PyString::new(py, if value { "1" } else { "0" }).into_any()
}

fn exact_str<'a>(part: &'a Bound<'_, PyAny>) -> Option<&'a str> {
    part.cast_exact::<PyString>()
        .ok()
        .and_then(|text| text.to_str().ok())
}

/// `int(text)` / `float(text)` for anything the plain-ASCII fast path does not take; a
/// `ValueError` there is a conversion error.
fn convert_text<'py>(
    py: Python<'py>,
    convert: &Bound<'py, PyAny>,
    part: &Bound<'py, PyAny>,
    what: &str,
) -> PyResult<Bound<'py, PyAny>> {
    convert.call1((part,)).map_err(|error| {
        if error.is_instance_of::<PyValueError>(py) {
            expected(py, what, part)
        } else {
            error
        }
    })
}

/// `int(text)` for plain ASCII digits with an optional sign; anything else goes through `int()`.
fn parse_int(text: &str) -> Option<i64> {
    let digits = text.strip_prefix(['+', '-']).unwrap_or(text);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

/// `float(text)` for plain decimal notation; `inf`, `nan`, `1_0`, spaces... go through `float()`.
fn parse_float(text: &str) -> Option<f64> {
    if text.is_empty()
        || !text
            .bytes()
            .all(|byte| byte.is_ascii_digit() || b"+-.eE".contains(&byte))
    {
        return None;
    }
    text.parse().ok()
}

#[cfg(test)]
mod tests {
    use super::{parse_float, parse_int};

    #[test]
    fn parse_int_takes_plain_digits_only() {
        assert_eq!(parse_int("42"), Some(42));
        assert_eq!(parse_int("-7"), Some(-7));
        assert_eq!(parse_int("+007"), Some(7));
        for text in ["", "+", "1_000", " 1", "١", "1.0", "99999999999999999999"] {
            assert_eq!(parse_int(text), None, "{text:?}");
        }
    }

    #[test]
    fn parse_float_takes_plain_decimals_only() {
        assert_eq!(parse_float("1.5"), Some(1.5));
        assert_eq!(parse_float("-2e3"), Some(-2000.0));
        assert_eq!(parse_float(".5"), Some(0.5));
        for text in ["", "inf", "nan", "1_0", " 1", "e", "1e"] {
            assert_eq!(parse_float(text), None, "{text:?}");
        }
    }
}
