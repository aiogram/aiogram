//! One pass: JSON text -> instance (`ModelConverter.load_json`), no intermediate dict.
//!
//! Builds what `json.loads` + `ModelConverter.from_json` would. Anything `jiter` and
//! `json.loads` might disagree on (NaN, integers outside `i64`, lone surrogates, a BOM...)
//! is a parse error here, so it falls back to `json.loads`.

use jiter::{Jiter, NumberAny, NumberInt, Peek, PythonParse};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyBytes, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};

use super::fallback::{Fallback, Fast};
use super::kind::Kind;
use super::schema::ModelSchema;

pub(crate) fn load_document<'py>(
    py: Python<'py>,
    data: &Bound<'py, PyAny>,
    schema: &ModelSchema,
) -> Fast<Bound<'py, PyAny>> {
    let text: &[u8] = if let Ok(bytes) = data.cast_exact::<PyBytes>() {
        bytes.as_bytes()
    } else if let Ok(string) = data.cast_exact::<PyString>() {
        string.to_str()?.as_bytes() // lone surrogates fail here and fall back
    } else {
        return Err(Fallback);
    };
    let mut parser = Jiter::new(text);
    let peek = parser.peek()?;
    let instance = load_model(py, &mut parser, text, peek, schema)?;
    parser.finish()?;
    Ok(instance)
}

fn load_model<'py>(
    py: Python<'py>,
    parser: &mut Jiter,
    text: &[u8],
    peek: Peek,
    schema: &ModelSchema,
) -> Fast<Bound<'py, PyAny>> {
    if peek != Peek::Object {
        return Err(Fallback);
    }
    let mut values: Vec<Option<Bound<'py, PyAny>>> = Vec::with_capacity(schema.fields.len());
    values.resize_with(schema.fields.len(), || None);
    let mut expected = 0usize; // keys usually come in field order
    let mut key = parser.known_object()?.map(str::to_owned);
    while let Some(name) = key {
        let peek = parser.peek()?;
        let index = match schema.fields.get(expected) {
            Some(field) if field.key == name => Some(expected),
            _ => schema.fields.iter().position(|field| field.key == name),
        };
        match index {
            Some(index) => {
                // a repeated key: the last one wins, as in json.loads
                values[index] = Some(load(py, parser, text, peek, &schema.fields[index].kind)?);
                expected = index + 1;
            }
            None => parser.known_skip(peek)?,
        }
        key = parser.next_key()?.map(str::to_owned);
    }
    schema.build(py, values)
}

/// Any JSON value as `json.loads` returns it (for converters called from Rust).
fn any_value<'py>(
    py: Python<'py>,
    parser: &mut Jiter,
    text: &[u8],
    peek: Peek,
) -> Fast<Bound<'py, PyAny>> {
    if peek == Peek::String {
        return Ok(PyString::new(py, parser.known_str()?).into_any());
    }
    let start = parser.current_index();
    parser.known_skip(peek)?;
    let slice = text.get(start..parser.current_index()).ok_or(Fallback)?;
    PythonParse::default()
        .python_parse(py, slice)
        .map_err(|_| Fallback)
}

fn load<'py>(
    py: Python<'py>,
    parser: &mut Jiter,
    text: &[u8],
    peek: Peek,
    kind: &Kind,
) -> Fast<Bound<'py, PyAny>> {
    match kind {
        Kind::Str if peek == Peek::String => Ok(PyString::new(py, parser.known_str()?).into_any()),
        Kind::Int if peek.is_num() => match parser.known_number(peek)? {
            NumberAny::Int(NumberInt::Int(int)) => Ok(PyInt::new(py, int).into_any()),
            NumberAny::Float(_) => Err(Fallback),
        },
        Kind::Float if peek.is_num() => match parser.known_number(peek)? {
            #[allow(clippy::cast_precision_loss)] // the same round-to-nearest as float(int)
            NumberAny::Int(NumberInt::Int(int)) => Ok(PyFloat::new(py, int as f64).into_any()),
            NumberAny::Float(float) => Ok(PyFloat::new(py, float).into_any()),
        },
        Kind::Bool if peek == Peek::True || peek == Peek::False => {
            Ok(PyBool::new(py, parser.known_bool(peek)?)
                .to_owned()
                .into_any())
        }
        Kind::Optional { .. } if peek == Peek::Null => {
            parser.known_null()?;
            Ok(py.None().into_bound(py))
        }
        Kind::Optional { inner, .. } => load(py, parser, text, peek, inner),
        Kind::Enum { by_value, .. } if peek != Peek::Array && peek != Peek::Object => {
            let value = any_value(py, parser, text, peek)?;
            by_value.bind(py).get_item(&value)?.ok_or(Fallback)
        }
        Kind::Literal { json, .. } if peek != Peek::Array && peek != Peek::Object => {
            let value = any_value(py, parser, text, peek)?;
            let key = PyTuple::new(py, [value.get_type().into_any(), value.clone()])?;
            match json.bind(py).contains(key)? {
                true => Ok(value),
                false => Err(Fallback),
            }
        }
        Kind::Sequence { item, collect } if peek == Peek::Array => {
            let out = PyList::empty(py);
            let mut next = parser.known_array()?;
            while let Some(peek) = next {
                out.append(load(py, parser, text, peek, item)?)?;
                next = parser.array_step()?;
            }
            Ok(collect.finish(out)?)
        }
        Kind::Dict(item) if peek == Peek::Object => {
            let out = PyDict::new(py);
            let mut key = parser.known_object()?.map(str::to_owned);
            while let Some(name) = key {
                let peek = parser.peek()?;
                out.set_item(
                    PyString::new(py, &name),
                    load(py, parser, text, peek, item)?,
                )?;
                key = parser.next_key()?.map(str::to_owned);
            }
            Ok(out.into_any())
        }
        Kind::Model(nested) => {
            let schema = nested.schema(py)?;
            load_model(py, parser, text, peek, schema.get())
        }
        Kind::Python(converter) => {
            let value = any_value(py, parser, text, peek)?;
            Ok(converter
                .bind(py)
                .call_method1(pyo3::intern!(py, "from_json"), (value,))?)
        }
        _ => Err(Fallback),
    }
}
