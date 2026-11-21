//! The positional flat-string codec (callback data): one `str` part per field, fail-fast.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyFloat, PyInt, PyList, PyString};

use crate::conv::construct;
use crate::conv::errors::{VResult, ValError, expected, from_user};
use crate::conv::ir::{Data, Kind, UUID, json_type, std_type};
use crate::conv::model::ModelCore;
use crate::conv::native::{base64, number, uuid};
use crate::conv::scalars::{self, Num, TextIn};

/// `TypeError` for a field without a flat form, or with an explicit key.
pub(crate) fn check(py: Python<'_>, core: &ModelCore) -> PyResult<()> {
    if core.is_dict() {
        return Err(PyTypeError::new_err(format!(
            "{} is a TypedDict, which has no flat-string form",
            core.qualname
        )));
    }
    for field in &core.fields(py)?.list {
        let field = field.get();
        let kind = field.kind.get();
        let name = field.name.bind(py);
        if !kind.flat {
            return Err(PyTypeError::new_err(format!(
                "{}.{name}: {} has no flat-string form",
                core.qualname, kind.label
            )));
        }
        if field.keyed {
            return Err(PyTypeError::new_err(format!(
                "{}.{name}: callback data is packed by position; Key and rename have no effect",
                core.qualname
            )));
        }
    }
    Ok(())
}

fn no_flat(kind: &Kind) -> ValError {
    ValError::Fatal(PyTypeError::new_err(format!(
        "{} has no flat-string form",
        kind.label
    )))
}

/// `int(text)` for plain ASCII digits with an optional sign.
fn parse_int(text: &str) -> Option<i64> {
    let digits = text.strip_prefix(['+', '-']).unwrap_or(text);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

/// `float(text)` for plain decimal notation (no `inf`, `nan`, `_`, spaces).
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

/// `int(part)`; `None` on a `ValueError`.
fn int_of<'py>(part: &Bound<'py, PyString>) -> PyResult<Option<Bound<'py, PyAny>>> {
    let py = part.py();
    if let Some(int) = part.to_str().ok().and_then(parse_int) {
        return Ok(Some(PyInt::new(py, int).into_any()));
    }
    match py.get_type::<PyInt>().call1((part,)) {
        Ok(int) => Ok(Some(int)),
        Err(error) if error.is_instance_of::<PyValueError>(py) => Ok(None),
        Err(error) => Err(error),
    }
}

/// `float(part)`; `None` on a `ValueError`.
fn float_of<'py>(part: &Bound<'py, PyString>) -> PyResult<Option<Bound<'py, PyAny>>> {
    let py = part.py();
    if let Some(float) = part.to_str().ok().and_then(parse_float) {
        return Ok(Some(PyFloat::new(py, float).into_any()));
    }
    match py.get_type::<PyFloat>().call1((part,)) {
        Ok(float) => Ok(Some(float)),
        Err(error) if error.is_instance_of::<PyValueError>(py) => Ok(None),
        Err(error) => Err(error),
    }
}

const TRUE: [&str; 6] = ["1", "true", "t", "yes", "y", "on"];
const FALSE: [&str; 6] = ["0", "false", "f", "no", "n", "off"];

/// The flat load of one part.
pub(crate) fn load<'py>(
    py: Python<'py>,
    part: &Bound<'py, PyAny>,
    kind: &Kind,
) -> VResult<Bound<'py, PyAny>> {
    let label = kind.label.as_str();
    let text = part.cast::<PyString>().map_err(|_| expected(label, part))?;
    match &kind.data {
        Data::Str => Ok(part.clone()),
        Data::Int => int_of(text)?.ok_or_else(|| expected(label, part)),
        Data::Float => float_of(text)?.ok_or_else(|| expected(label, part)),
        Data::Bool => {
            // the lax set, matched as `text.lower()`: only ASCII letters can lower to its words
            let text = text.to_str().unwrap_or_default();
            if TRUE.iter().any(|word| word.eq_ignore_ascii_case(text)) {
                Ok(scalars::py_bool(py, true))
            } else if FALSE.iter().any(|word| word.eq_ignore_ascii_case(text)) {
                Ok(scalars::py_bool(py, false))
            } else {
                Err(expected(label, part))
            }
        }
        Data::Uuid { .. } => scalars::load_text(py, kind, TextIn::Py(text)),
        Data::Timedelta => {
            let number = match int_of(text)? {
                Some(int) => int,
                None => float_of(text)?.ok_or_else(|| expected(label, part))?,
            };
            scalars::load_timedelta(&number, label).map_err(|error| match error {
                ValError::Lines(_) => expected(label, part),
                fatal @ ValError::Fatal(_) => fatal,
            })
        }
        Data::Decimal { .. } => scalars::decimal(py, part, label),
        Data::Bytes => match text
            .to_str()
            .ok()
            .and_then(|text| base64::decode(text, true))
        {
            Some(data) => Ok(pyo3::types::PyBytes::new(py, &data).into_any()),
            None => Err(expected(label, part)),
        },
        Data::Text(text) if kind.flat => scalars::parse_text(text, part, label),
        Data::Enum(enumeration) => {
            let table = enumeration.text.as_ref().ok_or_else(|| no_flat(kind))?;
            if let Some(member) = table.bind(py).get_item(part)? {
                return Ok(member);
            }
            let converted = if kind.json_types == json_type::INT {
                match int_of(text)? {
                    Some(int) => int,
                    None => return Err(expected(label, part)),
                }
            } else {
                part.clone()
            };
            scalars::enum_missing(enumeration, &converted)?.ok_or_else(|| expected(label, part))
        }
        Data::Literal(literal) => {
            let table = literal.text.as_ref().ok_or_else(|| no_flat(kind))?;
            table
                .bind(py)
                .get_item(part)?
                .ok_or_else(|| expected(label, part))
        }
        Data::Optional(inner) => {
            if text.to_str().is_ok_and(str::is_empty) {
                Ok(py.None().into_bound(py))
            } else {
                load(py, part, inner.get())
            }
        }
        Data::Python {
            converter,
            flat: true,
        } => converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "from_str"), (part,))
            .map_err(|error| from_user(py, error, part)),
        Data::Lazy(_) => load(py, part, kind.resolved(py)?),
        _ => Err(no_flat(kind)),
    }
}

/// The flat dump of one value.
pub(crate) fn dump<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
) -> VResult<Bound<'py, PyString>> {
    let label = kind.label.as_str();
    let text = |bytes: &[u8]| PyString::new(py, std::str::from_utf8(bytes).unwrap_or_default());
    Ok(match &kind.data {
        Data::Str => value
            .cast::<PyString>()
            .map_err(|_| expected(label, value))?
            .clone(),
        Data::Int => scalars::int(value, label)?.str()?,
        Data::Float => {
            let float = scalars::float_value(value, label)?;
            if float.is_finite() {
                let mut out = Vec::new();
                number::write_float(float, &mut out);
                text(&out)
            } else {
                PyFloat::new(py, float).repr()? // nan, inf, -inf
            }
        }
        Data::Bool => {
            let flag = scalars::boolean(value, label)?.is_truthy()?;
            PyString::new(py, if flag { "1" } else { "0" })
        }
        Data::Uuid { .. } => {
            if !value.is_instance(std_type(py, &UUID, "uuid", "UUID")?)? {
                return Err(expected(label, value));
            }
            let mut out = String::new();
            uuid::write(scalars::uuid_int(value)?, true, &mut out);
            PyString::new(py, &out)
        }
        Data::Timedelta => {
            let mut out = Vec::new();
            match scalars::dump_timedelta(value, label)? {
                Num::Obj(float) => Num::Float(float.extract()?).write(&mut out)?,
                number => number.write(&mut out)?,
            }
            text(&out)
        }
        Data::Decimal { .. } => {
            let mut out = String::new();
            scalars::dump_text(py, value, kind, &mut out)?;
            PyString::new(py, &out)
        }
        Data::Bytes => {
            let bytes = value
                .cast::<pyo3::types::PyBytes>()
                .map_err(|_| expected(label, value))?;
            PyString::new(py, &base64::encode(bytes.as_bytes(), true))
        }
        Data::Text(text) if kind.flat => scalars::format_text(text, value, label)?,
        Data::Enum(enumeration) if enumeration.text.is_some() => {
            let dumped = scalars::dump_enum(enumeration, value, label)?;
            dumped.str()?
        }
        Data::Literal(literal) if literal.text.is_some() => {
            scalars::check_literal(literal, value, label)?;
            if value.is_none() {
                PyString::new(py, "")
            } else if let Ok(flag) = value.cast::<pyo3::types::PyBool>() {
                PyString::new(py, if flag.is_true() { "1" } else { "0" })
            } else {
                value.str()?
            }
        }
        Data::Optional(inner) => {
            if value.is_none() {
                PyString::new(py, "")
            } else {
                dump(py, value, inner.get())?
            }
        }
        Data::Python {
            converter,
            flat: true,
        } => {
            let result = converter
                .bind(py)
                .call_method1(pyo3::intern!(py, "to_str"), (value,))
                .map_err(|error| from_user(py, error, value))?;
            result.cast_into::<PyString>().map_err(|error| {
                ValError::Fatal(PyTypeError::new_err(format!(
                    "{label}.to_str returned {}, not str",
                    error
                        .into_inner()
                        .get_type()
                        .name()
                        .map_or_else(|_| String::from("?"), |name| name.to_string())
                )))
            })?
        }
        Data::Lazy(_) => dump(py, value, kind.resolved(py)?)?,
        _ => return Err(no_flat(kind)),
    })
}

/// `FlatSchema.load`: one part per field, in order.
pub(crate) fn load_parts<'py>(
    py: Python<'py>,
    core: &ModelCore,
    parts: &Bound<'py, PyAny>,
) -> VResult<Bound<'py, PyAny>> {
    let fields = core.fields(py)?;
    let parts = PyList::new(py, parts.try_iter()?.collect::<PyResult<Vec<_>>>()?)?;
    if parts.len() != fields.list.len() {
        return Err(ValError::new(
            format!("expected {} parts", fields.list.len()),
            Some(parts.as_any()),
        ));
    }
    let mut slots = Vec::with_capacity(fields.list.len());
    for (field, part) in fields.list.iter().zip(parts.iter()) {
        let field = field.get();
        let value =
            load(py, &part, field.kind.get()).map_err(|error| error.at_key(py, &field.key))?;
        slots.push((Some(value), true));
    }
    construct::build(py, core, fields, slots, &|| Ok(parts.clone().into_any()))
}

/// `FlatSchema.dump`: an instance of the class -> one part per field.
pub(crate) fn dump_parts<'py>(
    py: Python<'py>,
    core: &ModelCore,
    obj: &Bound<'py, PyAny>,
) -> VResult<Bound<'py, PyList>> {
    let fields = core.fields(py)?;
    if !obj.is_instance(core.tp.bind(py))? {
        return Err(expected(&core.qualname, obj));
    }
    let mut parts = Vec::with_capacity(fields.list.len());
    for field in &fields.list {
        let field = field.get();
        let value = obj.getattr(&field.name)?;
        parts.push(
            dump(py, &value, field.kind.get()).map_err(|error| error.at_key(py, &field.key))?,
        );
    }
    Ok(PyList::new(py, parts)?)
}

#[cfg(test)]
mod tests {
    use super::{parse_float, parse_int};

    #[test]
    fn parse_int_takes_plain_digits_only() {
        assert_eq!(parse_int("42"), Some(42));
        assert_eq!(parse_int("-7"), Some(-7));
        assert_eq!(parse_int("+007"), Some(7));
        for text in [
            "",
            "+",
            "1_000",
            " 1",
            "\u{661}",
            "1.0",
            "99999999999999999999",
        ] {
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
