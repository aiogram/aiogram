//! One pass: JSON text -> instance (`ModelConverter.load_json`), no intermediate dict.
//!
//! Gives what `json.loads` + `from_json` would: NaN / Infinity and integers of any size are
//! accepted, a UTF-8 BOM is skipped, the last of repeated keys wins. Scalars, sequences, dicts,
//! TypedDicts and models are walked here. Any other kind, and any value of the wrong JSON type,
//! is materialised and handed to [`load::load`], so the error is the `from_json` one. Invalid
//! JSON is a `ConversionError("invalid JSON: ...")`. With several invalid fields, the first in
//! document order is reported.

use jiter::{Jiter, JiterError, LinePosition, NumberAny, NumberInt, Peek, PythonParse};
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyByteArray, PyBytes, PyDict, PyFloat, PyInt, PyList, PyString};

use super::errors::{self, at};
use super::kind::{Data, Kind};
use super::load::{self, float};
use super::schema::ModelSchema;

struct Document<'a> {
    parser: Jiter<'a>,
    text: &'a [u8],
}

pub(crate) fn load_document<'py>(
    py: Python<'py>,
    data: &Bound<'py, PyAny>,
    schema: &ModelSchema,
) -> PyResult<Bound<'py, PyAny>> {
    let owned: Vec<u8>;
    let encoded; // a temporary copy: `to_str` would cache UTF-8 on the str for its lifetime
    let text: &[u8] = if let Ok(bytes) = data.cast_exact::<PyBytes>() {
        bytes.as_bytes()
    } else if let Ok(array) = data.cast_exact::<PyByteArray>() {
        owned = array.to_vec();
        &owned
    } else if let Ok(string) = data.cast_exact::<PyString>() {
        encoded = string.encode_utf8()?;
        encoded.as_bytes()
    } else {
        let name = data.get_type().name()?;
        return Err(PyTypeError::new_err(format!(
            "the JSON object must be str, bytes or bytearray, not {name}"
        )));
    };
    let text = text.strip_prefix(b"\xef\xbb\xbf").unwrap_or(text);
    let mut document = Document {
        parser: Jiter::new(text).with_allow_inf_nan(),
        text,
    };
    let peek = document.peek(py)?;
    let instance = model(py, &mut document, peek, schema, 0)?;
    document
        .parser
        .finish()
        .map_err(|e| syntax(py, document.text, &e))?;
    Ok(instance)
}

/// Invalid JSON: `ConversionError("invalid JSON: <problem> at line L column C")`.
fn syntax(py: Python<'_>, text: &[u8], error: &JiterError) -> PyErr {
    let position = LinePosition::find(text, error.index);
    let reason = format!(
        "invalid JSON: {} at line {} column {}",
        error.error_type, position.line, position.column
    );
    errors::conversion(py, &reason, None)
}

impl Document<'_> {
    fn peek(&mut self, py: Python<'_>) -> PyResult<Peek> {
        let text = self.text;
        self.parser.peek().map_err(|e| syntax(py, text, &e))
    }

    fn key(&mut self, py: Python<'_>, first: bool) -> PyResult<Option<String>> {
        let text = self.text;
        let key = if first {
            self.parser.known_object()
        } else {
            self.parser.next_key()
        };
        key.map(|key| key.map(str::to_owned))
            .map_err(|e| syntax(py, text, &e))
    }

    /// Any JSON value as `json.loads` returns it.
    fn value<'py>(&mut self, py: Python<'py>, peek: Peek) -> PyResult<Bound<'py, PyAny>> {
        let text = self.text;
        if peek == Peek::String {
            let text = self.parser.known_str().map_err(|e| syntax(py, text, &e))?;
            return Ok(PyString::new(py, text).into_any());
        }
        let start = self.parser.current_index();
        self.parser
            .known_skip(peek)
            .map_err(|e| syntax(py, text, &e))?;
        let slice = &text[start..self.parser.current_index()];
        let parse = PythonParse {
            allow_inf_nan: true,
            ..PythonParse::default()
        };
        parse
            .python_parse(py, slice)
            .map_err(|e| errors::conversion(py, &format!("invalid JSON: {e}"), None))
    }

    fn number<'py>(&mut self, py: Python<'py>, peek: Peek) -> PyResult<Bound<'py, PyAny>> {
        let text = self.text;
        Ok(
            match self
                .parser
                .known_number(peek)
                .map_err(|e| syntax(py, text, &e))?
            {
                NumberAny::Int(NumberInt::Int(int)) => PyInt::new(py, int).into_any(),
                NumberAny::Int(NumberInt::BigInt(big)) => {
                    py.get_type::<PyInt>().call1((big.to_string(),))?
                }
                NumberAny::Float(float) => PyFloat::new(py, float).into_any(),
            },
        )
    }
}

fn model<'py>(
    py: Python<'py>,
    document: &mut Document<'_>,
    peek: Peek,
    schema: &ModelSchema,
    depth: u32,
) -> PyResult<Bound<'py, PyAny>> {
    errors::check_depth(depth)?;
    if peek != Peek::Object {
        let value = document.value(py, peek)?;
        return schema.load(py, &value, depth);
    }
    let mut values: Vec<Option<Bound<'py, PyAny>>> = Vec::with_capacity(schema.fields.len());
    values.resize_with(schema.fields.len(), || None);
    let mut expected = 0usize; // keys usually come in field order
    let mut key = document.key(py, true)?;
    while let Some(name) = key {
        let peek = document.peek(py)?;
        let index = match schema.fields.get(expected) {
            Some(field) if field.key == name => Some(expected),
            _ => schema.fields.iter().position(|field| field.key == name),
        };
        match index {
            Some(index) => {
                let field = &schema.fields[index];
                let value = walk(py, document, peek, &field.kind, depth + 1)
                    .map_err(|e| at(py, e, || Ok(format!(".{}", field.key))))?;
                values[index] = Some(value);
                expected = index + 1;
            }
            None => document
                .parser
                .known_skip(peek)
                .map_err(|e| syntax(py, document.text, &e))?,
        }
        key = document.key(py, false)?;
    }
    let set: Vec<bool> = values.iter().map(Option::is_some).collect();
    let mut filled = Vec::with_capacity(values.len());
    for (field, value) in schema.fields.iter().zip(values) {
        filled.push(match value {
            Some(value) => value,
            None => schema.default(py, field)?,
        });
    }
    schema.build(py, filled, &set, None)
}

fn walk<'py>(
    py: Python<'py>,
    document: &mut Document<'_>,
    peek: Peek,
    kind: &Kind,
    depth: u32,
) -> PyResult<Bound<'py, PyAny>> {
    match &kind.data {
        Data::Str if peek == Peek::String => document.value(py, peek),
        Data::Int if peek.is_num() => {
            let value = document.number(py, peek)?;
            if value.is_exact_instance_of::<PyInt>() {
                Ok(value)
            } else {
                load::load(py, &value, kind, depth) // a float: "expected an integer"
            }
        }
        Data::Float if peek.is_num() => float(py, &document.number(py, peek)?),
        Data::Bool if peek == Peek::True || peek == Peek::False => {
            let value = document
                .parser
                .known_bool(peek)
                .map_err(|e| syntax(py, document.text, &e))?;
            Ok(PyBool::new(py, value).to_owned().into_any())
        }
        Data::Optional { .. } if peek == Peek::Null => {
            document
                .parser
                .known_null()
                .map_err(|e| syntax(py, document.text, &e))?;
            Ok(py.None().into_bound(py))
        }
        Data::Optional { inner, .. } => walk(py, document, peek, inner, depth),
        Data::Sequence { item, collect, .. } if peek == Peek::Array => {
            errors::check_depth(depth)?;
            let out = PyList::empty(py);
            let mut next = document
                .parser
                .known_array()
                .map_err(|e| syntax(py, document.text, &e))?;
            let mut index = 0usize;
            while let Some(peek) = next {
                let value = walk(py, document, peek, item, depth + 1)
                    .map_err(|e| at(py, e, || Ok(format!("[{index}]"))))?;
                out.append(value)?;
                index += 1;
                next = document
                    .parser
                    .array_step()
                    .map_err(|e| syntax(py, document.text, &e))?;
            }
            collect.finish(out)
        }
        Data::Dict(item) if peek == Peek::Object => {
            errors::check_depth(depth)?;
            let out = PyDict::new(py);
            let mut key = document.key(py, true)?;
            while let Some(name) = key {
                let peek = document.peek(py)?;
                let key_object = PyString::new(py, &name);
                let value = walk(py, document, peek, item, depth + 1)
                    .map_err(|e| at(py, e, || Ok(format!("[{}]", key_object.repr()?))))?;
                out.set_item(key_object, value)?;
                key = document.key(py, false)?;
            }
            Ok(out.into_any())
        }
        Data::TypedDict(typed) if peek == Peek::Object => {
            errors::check_depth(depth)?;
            let fields = typed.fields(py, &kind.converter)?;
            let mut values: Vec<Option<Bound<'py, PyAny>>> = Vec::with_capacity(fields.len());
            values.resize_with(fields.len(), || None);
            let mut key = document.key(py, true)?;
            while let Some(name) = key {
                let peek = document.peek(py)?;
                match fields.iter().position(|field| field.key == name) {
                    Some(index) => {
                        let field = &fields[index];
                        let value = walk(py, document, peek, &field.kind, depth + 1)
                            .map_err(|e| at(py, e, || Ok(format!(".{}", field.key))))?;
                        values[index] = Some(value);
                    }
                    None => document
                        .parser
                        .known_skip(peek)
                        .map_err(|e| syntax(py, document.text, &e))?,
                }
                key = document.key(py, false)?;
            }
            let out = PyDict::new(py);
            for (field, value) in fields.iter().zip(values) {
                match value {
                    Some(value) => out.set_item(field.name.bind(py), value)?,
                    None if field.required => {
                        let error = errors::conversion(py, "field required", None);
                        return Err(at(py, error, || Ok(format!(".{}", field.key))));
                    }
                    None => {}
                }
            }
            Ok(out.into_any())
        }
        Data::Model(nested) => model(
            py,
            document,
            peek,
            nested.schema(py, &kind.converter)?.get(),
            depth + 1,
        ),
        _ => {
            // other kinds, and every value of the wrong JSON type: the from_json path
            let value = document.value(py, peek)?;
            load::load(py, &value, kind, depth)
        }
    }
}
