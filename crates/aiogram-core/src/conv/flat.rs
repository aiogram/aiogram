//! Flat codec: callback-data parts <-> instance (`ModelConverter.from_flat` / `to_flat`).

use pyo3::prelude::*;
use pyo3::types::{PyBool, PyFloat, PyInt, PyList, PyString, PyTuple};

use super::fallback::{Fallback, Fast};
use super::kind::Kind;
use super::schema::ModelSchema;

pub(crate) fn from_parts<'py>(
    py: Python<'py>,
    parts: &Bound<'py, PyAny>,
    schema: &ModelSchema,
) -> Fast<Bound<'py, PyAny>> {
    let parts: Vec<Bound<'py, PyAny>> = if let Ok(list) = parts.cast_exact::<PyList>() {
        list.iter().collect()
    } else if let Ok(tuple) = parts.cast_exact::<PyTuple>() {
        tuple.iter().collect()
    } else {
        return Err(Fallback::Retry);
    };
    if parts.len() != schema.fields.len() {
        return Err(Fallback::Retry);
    }
    let mut values = Vec::with_capacity(parts.len());
    for (field, part) in schema.fields.iter().zip(&parts) {
        let text = part.cast_exact::<PyString>().map_err(|_| Fallback::Retry)?;
        values.push(Some(from_str(py, text, &field.kind)?));
    }
    schema.build(py, values)
}

fn from_str<'py>(
    py: Python<'py>,
    part: &Bound<'py, PyString>,
    kind: &Kind,
) -> Fast<Bound<'py, PyAny>> {
    match kind {
        Kind::Str => Ok(part.clone().into_any()),
        Kind::Int => {
            Ok(PyInt::new(py, parse_int(part.to_str()?).ok_or(Fallback::Retry)?).into_any())
        }
        Kind::Float => {
            Ok(PyFloat::new(py, parse_float(part.to_str()?).ok_or(Fallback::Retry)?).into_any())
        }
        Kind::Bool => match part.to_str()? {
            "1" => Ok(PyBool::new(py, true).to_owned().into_any()),
            "0" => Ok(PyBool::new(py, false).to_owned().into_any()),
            _ => Err(Fallback::Retry), // the lax set ("true", "Off", ...) stays in Python
        },
        Kind::Optional { flat: true, .. } if part.to_str()?.is_empty() => {
            Ok(py.None().into_bound(py))
        }
        Kind::Optional { inner, flat: true } => from_str(py, part, inner),
        Kind::Enum {
            by_text: Some(by_text),
            ..
        } => by_text.bind(py).get_item(part)?.ok_or(Fallback::Retry),
        Kind::Literal {
            text: Some(text), ..
        } => text.bind(py).get_item(part)?.ok_or(Fallback::Retry),
        Kind::Python(converter) => Ok(converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "from_str"), (part,))?),
        _ => Err(Fallback::Retry), // no flat-string form: Python raises TypeError
    }
}

pub(crate) fn to_parts<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    schema: &ModelSchema,
) -> Fast<Bound<'py, PyList>> {
    if !value.is_instance(schema.cls(py))? {
        return Err(Fallback::Retry);
    }
    let parts = PyList::empty(py);
    for field in &schema.fields {
        parts.append(to_str(
            py,
            &value.getattr(field.name.bind(py))?,
            &field.kind,
        )?)?;
    }
    Ok(parts)
}

fn to_str<'py>(py: Python<'py>, value: &Bound<'py, PyAny>, kind: &Kind) -> Fast<Bound<'py, PyAny>> {
    match kind {
        Kind::Str if value.is_instance_of::<PyString>() => Ok(value.clone()),
        Kind::Int if value.is_exact_instance_of::<PyInt>() => Ok(value.str()?.into_any()),
        Kind::Float if value.is_exact_instance_of::<PyFloat>() => Ok(value.str()?.into_any()),
        Kind::Bool if value.is_exact_instance_of::<PyBool>() => Ok(match value.is_truthy()? {
            true => pyo3::intern!(py, "1").clone().into_any(),
            false => pyo3::intern!(py, "0").clone().into_any(),
        }),
        Kind::Optional { flat: true, .. } if value.is_none() => {
            Ok(pyo3::intern!(py, "").clone().into_any())
        }
        Kind::Optional { inner, flat: true } => to_str(py, value, inner),
        Kind::Enum {
            tp,
            by_text: Some(_),
            ..
        } if value.is_instance(tp.bind(py))? => {
            Ok(value.getattr(pyo3::intern!(py, "value"))?.str()?.into_any())
        }
        Kind::Literal {
            json,
            text: Some(_),
        } => {
            let key = PyTuple::new(py, [value.get_type().into_any(), value.clone()])?;
            if !json.bind(py).contains(key)? {
                return Err(Fallback::Retry);
            }
            // `_literal_text`: None -> "", bool -> "1"/"0", else str(value)
            if value.is_none() {
                Ok(pyo3::intern!(py, "").clone().into_any())
            } else if value.is_exact_instance_of::<PyBool>() {
                to_str(py, value, &Kind::Bool)
            } else {
                Ok(value.str()?.into_any())
            }
        }
        Kind::Python(converter) => Ok(converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "to_str"), (value,))?),
        _ => Err(Fallback::Retry), // every rejection stays in Python
    }
}

/// `int(text)` for plain ASCII digits with an optional sign; anything else falls back.
fn parse_int(text: &str) -> Option<i64> {
    let digits = text.strip_prefix(['+', '-']).unwrap_or(text);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

/// `float(text)` for plain decimal notation; `inf`, `nan`, `1_0`, spaces... fall back.
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
