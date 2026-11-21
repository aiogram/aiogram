//! The bytes load: JSON text -> values in one jiter pass, with no intermediate Python values for
//! scalars, containers and models. Gives what the dict load gives on `json.loads(data)`; errors
//! are collected in the same pass, and invalid JSON anywhere wins over them.

use jiter::{
    Jiter, JiterError, JiterErrorType, JsonErrorType, LinePosition, NumberAny, NumberInt, Peek,
    PythonParse,
};
use pyo3::exceptions::{PyRecursionError, PyRuntimeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyByteArray, PyBytes, PyDict, PyFloat, PyInt, PyString};

use crate::conv::errors::{Ctx, MAX_ERRORS, VResult, ValError, expected};
use crate::conv::ir::{Data, Kind, Union, json_type};
use crate::conv::json::load::{self, collect};
use crate::conv::model::ModelCore;
use crate::conv::scalars::{self, TextIn};
use crate::conv::walk::Errors;
use crate::conv::{construct, errors};

/// A walk failure: invalid JSON (`problem`, byte index) or a conversion error.
enum Fail {
    Json(String, usize),
    /// A `\udXXX` escape of a lone surrogate: jiter rejects it, `json.loads` (and our own
    /// `dump_json` output) has it
    Surrogate(String, usize),
    Val(ValError),
}

impl Fail {
    /// Invalid JSON; jiter's own nesting limit (skipped and materialised values) is the depth
    /// guard's `RecursionError`.
    fn json(error: &JsonErrorType, index: usize) -> Self {
        if matches!(error, JsonErrorType::RecursionLimitExceeded) {
            Self::Val(ValError::Fatal(PyRecursionError::new_err(
                "maximum nesting depth exceeded while converting",
            )))
        } else if matches!(
            error,
            JsonErrorType::LoneLeadingSurrogateInHexEscape
                | JsonErrorType::UnexpectedEndOfHexEscape
        ) {
            Self::Surrogate(error.to_string(), index)
        } else {
            Self::Json(error.to_string(), index)
        }
    }
}

impl From<JiterError> for Fail {
    fn from(error: JiterError) -> Self {
        match &error.error_type {
            JiterErrorType::JsonError(json) => Self::json(json, error.index),
            other @ JiterErrorType::WrongType { .. } => Self::Json(other.to_string(), error.index),
        }
    }
}

impl From<ValError> for Fail {
    fn from(error: ValError) -> Self {
        Self::Val(error)
    }
}

impl From<PyErr> for Fail {
    fn from(error: PyErr) -> Self {
        Self::Val(ValError::Fatal(error))
    }
}

type PResult<T> = Result<T, Fail>;

fn invalid(data: &[u8], problem: &str, index: usize) -> ValError {
    let position = LinePosition::find(data, index);
    ValError::new(
        format!(
            "invalid JSON: {problem} at line {} column {}",
            position.line, position.column
        ),
        None,
    )
}

const BOM: &[u8] = b"\xef\xbb\xbf";

pub(crate) fn load_json<'py>(
    py: Python<'py>,
    data: &Bound<'py, PyAny>,
    kind: &Kind,
) -> VResult<Bound<'py, PyAny>> {
    let owned: Vec<u8>;
    let encoded: Bound<'py, PyBytes>;
    let text: &[u8] = if let Ok(bytes) = data.cast::<PyBytes>() {
        bytes
            .as_bytes()
            .strip_prefix(BOM)
            .unwrap_or(bytes.as_bytes())
    } else if let Ok(array) = data.cast::<PyByteArray>() {
        owned = array.to_vec();
        owned.strip_prefix(BOM).unwrap_or(&owned)
    } else if let Ok(string) = data.cast::<PyString>() {
        // a temporary copy: `to_str` would cache the UTF-8 form on the str for its lifetime
        encoded = string
            .encode_utf8()
            .map_err(|_| ValError::new("invalid JSON: the str contains a lone surrogate", None))?;
        encoded.as_bytes()
    } else {
        return Err(ValError::Fatal(PyTypeError::new_err(format!(
            "the JSON object must be str, bytes or bytearray, not {}",
            data.get_type().name()?
        ))));
    };
    // jiter does not check the UTF-8 of skipped strings
    if let Err(error) = std::str::from_utf8(text) {
        return Err(invalid(text, "invalid UTF-8", error.valid_up_to()));
    }
    let mut doc = Doc {
        jiter: Jiter::new(text).with_allow_inf_nan(),
        data: text,
    };
    let walked = doc
        .jiter
        .peek()
        .map_err(Fail::from)
        .and_then(|peek| walk(py, &mut doc, peek, kind, Ctx::new(false)));
    let failed = match walked {
        Ok(value) => match doc.jiter.finish() {
            Ok(()) => return Ok(value),
            Err(error) => Fail::from(error),
        },
        Err(Fail::Val(ValError::Lines(lines))) => {
            // the walk may have stopped early (error cap): invalid JSON later still wins
            let mut check = Jiter::new(text).with_allow_inf_nan();
            match check
                .next_skip()
                .and_then(|()| check.finish())
                .map_err(Fail::from)
            {
                Err(json @ (Fail::Json(..) | Fail::Surrogate(..))) => json,
                // valid, or too deep for the skip: the lines stand
                _ => Fail::Val(ValError::Lines(lines)),
            }
        }
        Err(other) => other,
    };
    Err(match failed {
        Fail::Json(problem, index) => invalid(text, &problem, index),
        Fail::Surrogate(problem, index) => return surrogates(py, text, kind, &problem, index),
        Fail::Val(error) => error,
    })
}

/// The rare document with lone-surrogate escapes: `json.loads`, then the dict load.
// ponytail: a second parse for this input only; a jiter option would make it one pass
fn surrogates<'py>(
    py: Python<'py>,
    text: &[u8],
    kind: &Kind,
    problem: &str,
    index: usize,
) -> VResult<Bound<'py, PyAny>> {
    let value = py
        .import(pyo3::intern!(py, "json"))?
        .call_method1(pyo3::intern!(py, "loads"), (PyBytes::new(py, text),));
    match value {
        Ok(value) => load::load(py, &value, kind, Ctx::new(false)),
        Err(error) if error.is_instance_of::<pyo3::exceptions::PyValueError>(py) => {
            Err(invalid(text, problem, index))
        }
        Err(error) => Err(ValError::Fatal(error)),
    }
}

struct Doc<'j> {
    jiter: Jiter<'j>,
    data: &'j [u8],
}

impl Doc<'_> {
    /// Any JSON value as `json.loads` returns it.
    fn value<'py>(&mut self, py: Python<'py>, peek: Peek) -> PResult<Bound<'py, PyAny>> {
        match peek {
            Peek::Null => {
                self.jiter.known_null()?;
                Ok(py.None().into_bound(py))
            }
            Peek::True | Peek::False => Ok(scalars::py_bool(py, self.jiter.known_bool(peek)?)),
            Peek::String => Ok(PyString::new(py, self.jiter.known_str()?).into_any()),
            _ if peek.is_num() => self.number(py, peek),
            _ => {
                let start = self.jiter.current_index();
                self.jiter.known_skip(peek)?;
                parse_slice(py, self.data, start, self.jiter.current_index())
            }
        }
    }

    fn number<'py>(&mut self, py: Python<'py>, peek: Peek) -> PResult<Bound<'py, PyAny>> {
        Ok(match self.jiter.known_number(peek)? {
            NumberAny::Int(NumberInt::Int(int)) => PyInt::new(py, int).into_any(),
            NumberAny::Int(NumberInt::BigInt(big)) => {
                py.get_type::<PyInt>().call1((big.to_string(),))?
            }
            NumberAny::Float(float) => PyFloat::new(py, float).into_any(),
        })
    }

    /// Walk an array: `each(doc, peek, index)` for every item.
    fn array(
        &mut self,
        mut each: impl FnMut(&mut Self, Peek, usize) -> PResult<()>,
    ) -> PResult<()> {
        let mut next = self.jiter.known_array()?;
        let mut index = 0;
        while let Some(peek) = next {
            each(self, peek, index)?;
            index += 1;
            next = self.jiter.array_step()?;
        }
        Ok(())
    }
}

/// A conversion error of an item: kept (collecting) or returned (stop).
fn keep(
    errors: &mut Errors,
    error: Fail,
    ctx: Ctx,
    at: impl FnOnce(ValError) -> ValError,
) -> PResult<()> {
    match error {
        Fail::Val(error @ ValError::Lines(_)) => Ok(errors.push(at(error), ctx)?),
        other => Err(other),
    }
}

fn walk<'py>(
    py: Python<'py>,
    doc: &mut Doc<'_>,
    peek: Peek,
    kind: &Kind,
    ctx: Ctx,
) -> PResult<Bound<'py, PyAny>> {
    match &kind.data {
        _ if peek == Peek::String && scalars::is_text_kind(kind) => {
            let text = doc.jiter.known_str()?;
            Ok(scalars::load_text(py, kind, TextIn::Str(text))?)
        }
        Data::Int if peek.is_num() => match doc.jiter.known_number(peek)? {
            NumberAny::Int(NumberInt::Int(int)) => Ok(PyInt::new(py, int).into_any()),
            NumberAny::Int(NumberInt::BigInt(big)) => {
                Ok(py.get_type::<PyInt>().call1((big.to_string(),))?)
            }
            NumberAny::Float(float) => {
                Err(expected(&kind.label, &PyFloat::new(py, float).into_any()).into())
            }
        },
        Data::Float if peek.is_num() => match doc.jiter.known_number(peek)? {
            #[allow(clippy::cast_precision_loss)] // float(int) rounds the same way
            NumberAny::Int(NumberInt::Int(int)) => Ok(PyFloat::new(py, int as f64).into_any()),
            NumberAny::Int(NumberInt::BigInt(big)) => {
                let int = py.get_type::<PyInt>().call1((big.to_string(),))?;
                Ok(scalars::float(&int, &kind.label)?)
            }
            NumberAny::Float(float) => Ok(PyFloat::new(py, float).into_any()),
        },
        Data::Bool if peek == Peek::True || peek == Peek::False => {
            Ok(scalars::py_bool(py, doc.jiter.known_bool(peek)?))
        }
        Data::Decimal { number: true } if peek.is_num() => {
            // the number's source text: exact
            let text = std::str::from_utf8(doc.jiter.known_number_bytes(peek)?).unwrap_or_default();
            let text = PyString::new(py, text).into_any();
            Ok(scalars::decimal_number(py, &text, &kind.label)?)
        }
        Data::Optional(_) if peek == Peek::Null => {
            doc.jiter.known_null()?;
            Ok(py.None().into_bound(py))
        }
        Data::Optional(inner) => walk(py, doc, peek, inner.get(), ctx),
        Data::Sequence {
            item,
            collect: container,
        } if peek == Peek::Array => {
            let ctx = ctx.deeper()?;
            let mut out = Vec::new();
            let mut errors = Errors::new();
            doc.array(
                |doc, peek, index| match walk(py, doc, peek, item.get(), ctx) {
                    Ok(value) => {
                        out.push(value);
                        Ok(())
                    }
                    Err(error) => keep(&mut errors, error, ctx, |e| e.at_index(index)),
                },
            )?;
            errors.finish()?;
            Ok(collect(py, out, *container)?)
        }
        Data::Tuple(kinds) if peek == Peek::Array => {
            let ctx = ctx.deeper()?;
            let start = doc.jiter.current_index();
            let mut out = Vec::with_capacity(kinds.len());
            let mut errors = Errors::new();
            let mut length = 0;
            doc.array(|doc, peek, index| {
                length += 1;
                let Some(item) = kinds.get(index) else {
                    return Ok(doc.jiter.known_skip(peek)?);
                };
                match walk(py, doc, peek, item.get(), ctx) {
                    Ok(value) => {
                        out.push(value);
                        Ok(())
                    }
                    Err(error) => keep(&mut errors, error, ctx, |e| e.at_index(index)),
                }
            })?;
            if length != kinds.len() {
                let value = parse_slice(py, doc.data, start, doc.jiter.current_index())?;
                return Err(
                    ValError::new(format!("expected {} items", kinds.len()), Some(&value)).into(),
                );
            }
            errors.finish()?;
            Ok(pyo3::types::PyTuple::new(py, out)?.into_any())
        }
        Data::Dict(item) if peek == Peek::Object => dict(py, doc, item.get(), ctx),
        Data::Model(core) if peek == Peek::Object => {
            let core = core
                .get()
                .ok_or_else(|| PyRuntimeError::new_err("model kind cleared"))?;
            model(py, doc, core.get(), ctx)
        }
        Data::Lazy(_) => walk(py, doc, peek, kind.resolved(py)?, ctx.deeper()?),
        Data::Union(union) => self::union(py, doc, peek, union, &kind.label, ctx),
        // user converters, text, enums, literals, numbers of the number kinds, and every
        // value of the wrong JSON type: materialised, then the dict load
        _ => {
            let value = doc.value(py, peek)?;
            Ok(load::load(py, &value, kind, ctx)?)
        }
    }
}

fn dict<'py>(
    py: Python<'py>,
    doc: &mut Doc<'_>,
    item: &Kind,
    ctx: Ctx,
) -> PResult<Bound<'py, PyAny>> {
    let ctx = ctx.deeper()?;
    let out = PyDict::new(py);
    // errors by key: a repeated key replaces the earlier value and its errors
    let mut failed: Vec<(Bound<'py, PyString>, ValError)> = Vec::new();
    let mut count = 0;
    let mut key = doc.jiter.known_object()?.map(|key| PyString::new(py, key));
    while let Some(name) = key {
        let peek = doc.jiter.peek()?;
        let result = walk(py, doc, peek, item, ctx);
        if !failed.is_empty() {
            let mut kept = Vec::with_capacity(failed.len());
            for (known, error) in failed.drain(..) {
                if known.as_any().eq(&name)? {
                    count -= error.len();
                } else {
                    kept.push((known, error));
                }
            }
            failed = kept;
        }
        match result {
            Ok(value) => out.set_item(&name, value)?,
            Err(Fail::Val(error @ ValError::Lines(_))) => {
                if out.contains(&name)? {
                    out.del_item(&name)?;
                }
                count += error.len();
                let error = error.at(|| errors::Loc::Key(name.clone().unbind()));
                if ctx.fast || count >= MAX_ERRORS {
                    failed.push((name, error));
                    break;
                }
                failed.push((name, error));
            }
            Err(other) => return Err(other),
        }
        key = doc.jiter.next_key()?.map(|key| PyString::new(py, key));
    }
    let mut errors = Errors::new();
    for (_, error) in failed {
        errors.push(error, ctx)?;
    }
    errors.finish()?;
    Ok(out.into_any())
}

/// A field read from the document: the priority of its key, and its value or errors.
type Read<'py> = (usize, VResult<Bound<'py, PyAny>>);

fn model<'py>(
    py: Python<'py>,
    doc: &mut Doc<'_>,
    core: &ModelCore,
    ctx: Ctx,
) -> PResult<Bound<'py, PyAny>> {
    let ctx = ctx.deeper()?;
    let fields = core.fields(py)?;
    let start = doc.jiter.current_index();
    // per field: (priority of the key read, its value or errors)
    let mut read: Vec<Option<Read<'py>>> = fields.list.iter().map(|_| None).collect();
    let mut count = 0;
    let mut stopped = false;
    let mut next = doc
        .jiter
        .known_object()?
        .map(|key| fields.index.get(key).copied());
    while let Some(hit) = next {
        let peek = doc.jiter.peek()?;
        match hit {
            // a lower-priority key never replaces a higher one; the same key: the last one wins
            Some((index, priority))
                if read[index]
                    .as_ref()
                    .is_none_or(|(known, _)| priority <= *known) =>
            {
                let field = fields.list[index].get();
                let result = match walk(py, doc, peek, field.kind.get(), ctx) {
                    Ok(value) => Ok(value),
                    Err(Fail::Val(error @ ValError::Lines(_))) => Err(error.at_key(py, &field.key)),
                    Err(other) => return Err(other),
                };
                if let Some((_, Err(old))) = &read[index] {
                    count -= old.len();
                }
                if let Err(error) = &result {
                    count += error.len();
                }
                read[index] = Some((priority, result));
                if count > 0 && (ctx.fast || count >= MAX_ERRORS) {
                    stopped = true;
                    break;
                }
            }
            _ => doc.jiter.known_skip(peek)?,
        }
        next = doc
            .jiter
            .next_key()?
            .map(|key| fields.index.get(key).copied());
    }
    let mut slots = Vec::with_capacity(read.len());
    let mut errors = Errors::new();
    for (field, item) in fields.list.iter().zip(read) {
        match item {
            Some((_, Ok(value))) => slots.push((Some(value), true)),
            Some((_, Err(error))) => {
                errors.push(error, ctx)?;
                slots.push((None, true));
            }
            // keys after an early stop were not read: not "missing" (errors exist, no build)
            None if stopped => slots.push((None, false)),
            None => slots.push(load::missing(py, core, field.get(), &mut errors, ctx)?),
        }
    }
    errors.finish()?;
    // the value of a `__post_init__` / constructor error: the object, materialised on demand
    let end = doc.jiter.current_index();
    let data = doc.data;
    let input =
        || parse_slice(py, data, start, end).map_err(|_| PyRuntimeError::new_err("invalid JSON"));
    Ok(construct::build(py, core, fields, slots, &input)?)
}

/// `json.loads` of `data[start..end]` (a value already walked).
fn parse_slice<'py>(
    py: Python<'py>,
    data: &[u8],
    start: usize,
    end: usize,
) -> PResult<Bound<'py, PyAny>> {
    PythonParse {
        allow_inf_nan: true,
        ..PythonParse::default()
    }
    .python_parse(py, &data[start..end])
    .map_err(|error| Fail::json(&error.error_type, start + error.index))
}

/// The JSON type bits of a value from its source text (unions try exact matches first).
fn json_type_of(peek: Peek, text: &[u8]) -> u8 {
    match peek {
        Peek::Null => json_type::NULL,
        Peek::True | Peek::False => json_type::BOOL,
        Peek::String => json_type::STR,
        Peek::Array => json_type::ARRAY,
        Peek::Object => json_type::OBJECT,
        _ if text
            .iter()
            .any(|b| matches!(b, b'.' | b'e' | b'E' | b'N' | b'I')) =>
        {
            json_type::FLOAT
        }
        _ => json_type::INT,
    }
}

/// A union: the value's source text is walked again for each member tried, so every member sees
/// the exact JSON (a `DecimalAsNumber` member keeps its digits); the discriminator and the error
/// value use the materialised value.
fn union<'py>(
    py: Python<'py>,
    doc: &mut Doc<'_>,
    peek: Peek,
    union: &Union,
    label: &str,
    ctx: Ctx,
) -> PResult<Bound<'py, PyAny>> {
    if union.nullable && peek == Peek::Null {
        doc.jiter.known_null()?;
        return Ok(py.None().into_bound(py));
    }
    let start = doc.jiter.current_index();
    doc.jiter.known_skip(peek)?;
    let end = doc.jiter.current_index();
    let text = &doc.data[start..end];
    let member_walk = |member: &Kind, ctx: Ctx| -> PResult<Bound<'py, PyAny>> {
        let mut sub = Doc {
            jiter: Jiter::new(text).with_allow_inf_nan(),
            data: text,
        };
        let peek = sub.jiter.peek()?;
        walk(py, &mut sub, peek, member, ctx)
    };
    if union.discriminator.is_some() {
        let value = parse_slice(py, doc.data, start, end)?;
        let member = load::discriminated(py, union, label, &value)?;
        return member_walk(member, ctx);
    }
    let json_type = json_type_of(peek, text);
    let mut notes = Vec::new();
    for pass in [true, false] {
        for member in &union.members {
            let member = member.get();
            if (member.resolved(py)?.json_types & json_type != 0) != pass {
                continue;
            }
            match member_walk(member, ctx.fast()) {
                Ok(result) => return Ok(result),
                Err(Fail::Val(ValError::Lines(lines))) => {
                    if let Some(line) = lines.into_iter().next() {
                        notes.push((member.label.clone(), line));
                    }
                }
                Err(other) => return Err(other),
            }
        }
    }
    let value = parse_slice(py, doc.data, start, end)?;
    Err(Fail::Val(ValError::Lines(vec![errors::Line {
        loc: Vec::new(),
        message: format!("expected {label}"),
        value: Some(value.unbind()),
        cause: None,
        notes,
    }])))
}

#[cfg(test)]
mod tests {
    use pyo3::prelude::*;
    use pyo3::types::{PyBytes, PyDict, PyString};

    use super::load_json;
    use crate::conv::errors::{Loc, ValError};
    use crate::conv::ir::{Collect, Data, Kind, json_type};

    fn with_python(test: impl for<'py> FnOnce(Python<'py>)) {
        Python::initialize();
        Python::attach(test);
    }

    fn kind(data: Data, label: &str, json_types: u8) -> Kind {
        Kind {
            data,
            label: label.to_owned(),
            flat: false,
            json_types,
            py_types: Vec::new(),
        }
    }

    fn int(py: Python<'_>) -> Py<Kind> {
        Py::new(py, kind(Data::Int, "int", json_type::INT)).unwrap()
    }

    fn lines(error: ValError) -> Vec<(Vec<String>, String)> {
        let ValError::Lines(lines) = error else {
            panic!("fatal")
        };
        Python::attach(|py| {
            lines
                .into_iter()
                .map(|line| {
                    let loc = line
                        .loc
                        .iter()
                        .map(|segment| match segment {
                            Loc::Key(key) => key.bind(py).to_string(),
                            Loc::Index(index) => index.to_string(),
                        })
                        .collect();
                    (loc, line.message)
                })
                .collect()
        })
    }

    #[test]
    fn invalid_json_is_one_line_with_its_position() {
        with_python(|py| {
            let list = kind(
                Data::Sequence {
                    item: int(py),
                    collect: Collect::List,
                },
                "list",
                json_type::ARRAY,
            );
            for (data, message) in [
                (
                    &b"[1,\n 2,]"[..],
                    "invalid JSON: trailing comma at line 2 column 4",
                ),
                (
                    b"[\"a\", 1] x",
                    "invalid JSON: trailing characters at line 1 column 10",
                ),
                (
                    b"[1, \"\xff\"]",
                    "invalid JSON: invalid UTF-8 at line 1 column 6",
                ),
            ] {
                let error = load_json(py, PyBytes::new(py, data).as_any(), &list)
                    .err()
                    .unwrap();
                assert_eq!(lines(error), [(vec![], message.to_owned())]);
            }
            let loaded = load_json(py, PyBytes::new(py, b"\xef\xbb\xbf[1, 2]").as_any(), &list)
                .ok()
                .unwrap();
            assert_eq!(loaded.extract::<Vec<i64>>().unwrap(), [1, 2]);
            // a BOM is skipped for bytes only
            let text = PyString::new(py, "\u{feff}[1]");
            assert!(load_json(py, text.as_any(), &list).is_err());
        });
    }

    #[test]
    fn a_repeated_key_replaces_the_value_and_its_errors() {
        with_python(|py| {
            let dict = kind(Data::Dict(int(py)), "dict", json_type::OBJECT);
            let loaded = load_json(
                py,
                PyBytes::new(py, br#"{"a": "x", "a": 1, "b": 2}"#).as_any(),
                &dict,
            )
            .ok()
            .unwrap();
            let expected = PyDict::new(py);
            expected.set_item("a", 1).unwrap();
            expected.set_item("b", 2).unwrap();
            assert!(loaded.eq(expected).unwrap());
            let error = load_json(
                py,
                PyBytes::new(py, br#"{"a": 1, "a": "x", "b": "y"}"#).as_any(),
                &dict,
            )
            .err()
            .unwrap();
            assert_eq!(
                lines(error),
                [
                    (vec![String::from("a")], String::from("expected int")),
                    (vec![String::from("b")], String::from("expected int"))
                ]
            );
        });
    }
}
