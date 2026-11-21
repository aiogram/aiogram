//! The bytes dump: Python values -> compact JSON bytes, with the dump's rules and messages.

use pyo3::exceptions::{PyRecursionError, PyRuntimeError};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyBytes, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};

use crate::conv::errors::{Ctx, MAX_DEPTH, VResult, ValError, expected, field_required};
use crate::conv::ir::{Data, Kind, Union};
use crate::conv::json::dump::{fields_set, non_json, to_json};
use crate::conv::json::load::str_key_error;
use crate::conv::model::{Build, ModelCore};
use crate::conv::native::{number, string};
use crate::conv::scalars;
use crate::conv::walk::{self, Errors, dict_for_each};

pub(crate) fn dump_json(
    py: Python<'_>,
    value: &Bound<'_, PyAny>,
    kind: &Kind,
    ctx: Ctx,
) -> VResult<Vec<u8>> {
    let mut writer = Writer {
        out: Vec::with_capacity(128),
        text: String::new(),
    };
    writer.write(py, value, kind, ctx)?;
    Ok(writer.out)
}

struct Writer {
    out: Vec<u8>,
    /// Scratch buffer of the text kinds
    text: String,
}

/// Append a `str` as JSON; lone surrogates become `\udXXX` escapes.
fn write_py_str(text: &Bound<'_, PyString>, out: &mut Vec<u8>) -> PyResult<()> {
    if let Ok(utf8) = text.to_str() {
        string::write_str(utf8, out);
        return Ok(());
    }
    let units = text.call_method1(
        pyo3::intern!(text.py(), "encode"),
        ("utf-16-le", "surrogatepass"),
    )?;
    let units = units.cast_into::<PyBytes>()?;
    let units = units
        .as_bytes()
        .as_chunks::<2>()
        .0
        .iter()
        .map(|pair| u16::from_le_bytes(*pair));
    out.push(b'"');
    let mut run = String::new();
    let flush = |run: &mut String, out: &mut Vec<u8>| {
        if !run.is_empty() {
            let start = out.len();
            string::write_str(run, out);
            out.pop(); // the closing quote
            out.remove(start); // the opening quote
            run.clear();
        }
    };
    for unit in char::decode_utf16(units) {
        match unit {
            Ok(ch) => run.push(ch),
            Err(lone) => {
                flush(&mut run, out);
                out.extend_from_slice(format!("\\u{:04x}", lone.unpaired_surrogate()).as_bytes());
            }
        }
    }
    flush(&mut run, out);
    out.push(b'"');
    Ok(())
}

/// Write a user converter's output generically; `false` for a non-JSON value.
fn write_any(value: &Bound<'_, PyAny>, out: &mut Vec<u8>, depth: u32) -> PyResult<bool> {
    if depth > MAX_DEPTH {
        return Err(PyRecursionError::new_err(
            "maximum nesting depth exceeded while converting",
        ));
    }
    if value.is_none() {
        out.extend_from_slice(b"null");
    } else if let Ok(text) = value.cast::<PyString>() {
        write_py_str(text, out)?;
    } else if let Ok(flag) = value.cast::<PyBool>() {
        out.extend_from_slice(if flag.is_true() { b"true" } else { b"false" });
    } else if value.is_instance_of::<PyInt>() {
        scalars::write_int(value, out)?;
    } else if value.is_instance_of::<PyFloat>() {
        number::write_float(value.extract::<f64>()?, out);
    } else if let Ok(list) = value.cast::<PyList>() {
        return write_items(list.iter(), out, depth);
    } else if let Ok(tuple) = value.cast::<PyTuple>() {
        return write_items(tuple.iter(), out, depth);
    } else if let Ok(dict) = value.cast::<PyDict>() {
        out.push(b'{');
        let shaped = std::cell::Cell::new(true);
        let out_cell = std::cell::RefCell::new(std::mem::take(out));
        let result = dict_for_each(dict, |key, item| {
            let mut out = out_cell.borrow_mut();
            let Ok(key) = key.cast::<PyString>() else {
                shaped.set(false);
                return Err(ValError::Lines(Vec::new())); // stop
            };
            if out.last() != Some(&b'{') {
                out.push(b',');
            }
            write_py_str(key, &mut out)?;
            out.push(b':');
            if !write_any(&item, &mut out, depth + 1)? {
                shaped.set(false);
                return Err(ValError::Lines(Vec::new()));
            }
            Ok(())
        });
        *out = out_cell.into_inner();
        if let Err(ValError::Fatal(error)) = result {
            return Err(error);
        }
        out.push(b'}');
        return Ok(shaped.get());
    } else {
        return Ok(false);
    }
    Ok(true)
}

fn write_items<'py>(
    items: impl Iterator<Item = Bound<'py, PyAny>>,
    out: &mut Vec<u8>,
    depth: u32,
) -> PyResult<bool> {
    out.push(b'[');
    for (index, item) in items.enumerate() {
        if index > 0 {
            out.push(b',');
        }
        if !write_any(&item, out, depth + 1)? {
            return Ok(false);
        }
    }
    out.push(b']');
    Ok(true)
}

impl Writer {
    fn write(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        kind: &Kind,
        ctx: Ctx,
    ) -> VResult<()> {
        let label = kind.label.as_str();
        match &kind.data {
            Data::Optional(inner) => {
                if value.is_none() {
                    self.out.extend_from_slice(b"null");
                } else {
                    self.write(py, value, inner.get(), ctx)?;
                }
            }
            Data::Sequence { item, .. } => self.sequence(py, value, kind, item.get(), ctx)?,
            Data::Tuple(kinds) => self.tuple(py, value, kinds, label, ctx)?,
            Data::Dict(item) => self.dict(py, value, item.get(), label, ctx)?,
            Data::Model(core) => {
                let core = core
                    .get()
                    .ok_or_else(|| PyRuntimeError::new_err("model kind cleared"))?;
                self.model(py, value, core.get(), label, ctx)?;
            }
            Data::Union(union) => self.union(py, value, union, label, ctx)?,
            Data::Lazy(_) => self.write(py, value, kind.resolved(py)?, ctx)?,
            _ => self.scalar(py, value, kind, ctx)?,
        }
        Ok(())
    }

    /// The non-recursive kinds of [`Self::write`], out of line so the recursive frame stays small.
    #[inline(never)]
    fn scalar(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        kind: &Kind,
        ctx: Ctx,
    ) -> VResult<()> {
        let label = kind.label.as_str();
        match &kind.data {
            Data::Str => write_py_str(
                value
                    .cast::<PyString>()
                    .map_err(|_| expected(label, value))?,
                &mut self.out,
            )?,
            Data::Int => {
                if !value.is_instance_of::<PyInt>() || value.is_instance_of::<PyBool>() {
                    return Err(expected(label, value));
                }
                scalars::write_int(value, &mut self.out)?;
            }
            Data::Float => number::write_float(scalars::float_value(value, label)?, &mut self.out),
            Data::Bool => {
                let flag = value.cast::<PyBool>().map_err(|_| expected(label, value))?;
                self.out
                    .extend_from_slice(if flag.is_true() { b"true" } else { b"false" });
            }
            Data::Datetime {
                epoch: Some(epoch), ..
            } => scalars::dump_epoch(value, *epoch, label)?.write(&mut self.out)?,
            Data::Timedelta => scalars::dump_timedelta(value, label)?.write(&mut self.out)?,
            Data::Decimal { number: true } => self.decimal_number(value, kind)?,
            _ if scalars::is_text_kind(kind) => {
                self.text.clear();
                scalars::dump_text(py, value, kind, &mut self.text)?;
                string::write_str(&self.text, &mut self.out);
            }
            Data::Text(text) => {
                write_py_str(&scalars::format_text(text, value, label)?, &mut self.out)?
            }
            Data::Enum(enumeration) => {
                let dumped = scalars::dump_enum(enumeration, value, label)?;
                if !write_any(&dumped, &mut self.out, ctx.depth)? {
                    return Err(expected(label, value));
                }
            }
            Data::Literal(literal) => {
                scalars::check_literal(literal, value, label)?;
                if !write_any(value, &mut self.out, ctx.depth)? {
                    return Err(expected(label, value));
                }
            }
            Data::Python { converter, .. } => {
                let result = to_json(py, converter, value)?;
                let mark = self.out.len();
                if !write_any(&result, &mut self.out, ctx.depth)? {
                    self.out.truncate(mark);
                    return Err(non_json(label, &result));
                }
            }
            _ => {
                return Err(ValError::Fatal(PyRuntimeError::new_err(
                    "not a scalar kind",
                )));
            }
        }
        Ok(())
    }

    #[inline(never)] // keeps the recursive `write` frame small (the depth guard counts on it)
    fn sequence(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        kind: &Kind,
        item: &Kind,
        ctx: Ctx,
    ) -> VResult<()> {
        let label = kind.label.as_str();
        let container = kind
            .py_types
            .first()
            .ok_or_else(|| PyRuntimeError::new_err("sequence without a type"))?;
        if !value.is_instance(container.bind(py))? {
            return Err(expected(label, value));
        }
        let ctx = ctx.deeper()?;
        let mut errors = Errors::new();
        self.out.push(b'[');
        for (index, element) in value.try_iter()?.enumerate() {
            if index > 0 {
                self.out.push(b',');
            }
            if let Err(error) = self.write(py, &element?, item, ctx) {
                errors.push(error.at_index(index), ctx)?;
            }
        }
        self.out.push(b']');
        errors.finish()?;
        Ok(())
    }

    #[inline(never)] // keeps the recursive `write` frame small (the depth guard counts on it)
    fn tuple(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        kinds: &[Py<Kind>],
        label: &str,
        ctx: Ctx,
    ) -> VResult<()> {
        let tuple = value
            .cast::<PyTuple>()
            .map_err(|_| expected(label, value))?;
        if tuple.len() != kinds.len() {
            return Err(ValError::new(
                format!("expected {} items", kinds.len()),
                Some(value),
            ));
        }
        let ctx = ctx.deeper()?;
        let mut errors = Errors::new();
        self.out.push(b'[');
        for (index, (element, item)) in tuple.iter().zip(kinds).enumerate() {
            if index > 0 {
                self.out.push(b',');
            }
            if let Err(error) = self.write(py, &element, item.get(), ctx) {
                errors.push(error.at_index(index), ctx)?;
            }
        }
        self.out.push(b']');
        errors.finish()?;
        Ok(())
    }

    #[inline(never)] // keeps the recursive `write` frame small (the depth guard counts on it)
    fn dict(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        item: &Kind,
        label: &str,
        ctx: Ctx,
    ) -> VResult<()> {
        let source = value.cast::<PyDict>().map_err(|_| expected(label, value))?;
        let ctx = ctx.deeper()?;
        // collect the items first: the writer cannot be borrowed inside the critical section
        let items = std::cell::RefCell::new(Vec::with_capacity(source.len()));
        dict_for_each(source, |key, element| {
            items.borrow_mut().push((key, element));
            Ok(())
        })?;
        let items = items.into_inner();
        let mut errors = Errors::new();
        self.out.push(b'{');
        for (index, (key, element)) in items.iter().enumerate() {
            let Ok(name) = key.cast::<PyString>() else {
                errors.push(str_key_error(key)?, ctx)?;
                continue;
            };
            if index > 0 {
                self.out.push(b',');
            }
            write_py_str(name, &mut self.out)?;
            self.out.push(b':');
            if let Err(error) = self.write(py, element, item, ctx) {
                errors.push(
                    error.at(|| crate::conv::errors::Loc::Key(name.clone().unbind())),
                    ctx,
                )?;
            }
        }
        self.out.push(b'}');
        errors.finish()?;
        Ok(())
    }

    /// `str(d)` of a finite `Decimal`, written as a JSON number.
    fn decimal_number(&mut self, value: &Bound<'_, PyAny>, kind: &Kind) -> VResult<()> {
        scalars::finite_decimal(value, &kind.label)?;
        let text = value.str()?;
        self.out.extend_from_slice(text.to_str()?.as_bytes());
        Ok(())
    }

    fn model(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        core: &ModelCore,
        label: &str,
        ctx: Ctx,
    ) -> VResult<()> {
        let fields = core.fields(py)?;
        let source = if core.build == Build::Dict {
            Some(value.cast::<PyDict>().map_err(|_| expected(label, value))?)
        } else if value.is_instance(core.tp.bind(py))? {
            None
        } else {
            return Err(expected(label, value));
        };
        let set = fields_set(core, value, ctx)?;
        let ctx = ctx.deeper()?;
        let mut errors = Errors::new();
        let mut first = true;
        self.out.push(b'{');
        for field in &fields.list {
            let field = field.get();
            let name = field.name.bind(py);
            let attribute = match source {
                Some(dict) => match dict.get_item(name)? {
                    Some(item) => item,
                    None => {
                        if field.required {
                            errors.push(field_required(py, &field.key), ctx)?;
                        }
                        continue;
                    }
                },
                None => {
                    if let Some(set) = &set
                        && !set.contains(name)?
                    {
                        continue;
                    }
                    value.getattr(name)?
                }
            };
            if !first {
                self.out.push(b',');
            }
            first = false;
            write_py_str(field.key.bind(py), &mut self.out)?;
            self.out.push(b':');
            if let Err(error) = self.write(py, &attribute, field.kind.get(), ctx) {
                errors.push(error.at_key(py, &field.key), ctx)?;
            }
        }
        self.out.push(b'}');
        errors.finish()
    }

    fn union(
        &mut self,
        py: Python<'_>,
        value: &Bound<'_, PyAny>,
        union: &Union,
        label: &str,
        ctx: Ctx,
    ) -> VResult<()> {
        if union.nullable && value.is_none() {
            self.out.extend_from_slice(b"null");
            return Ok(());
        }
        let tp = value.get_type();
        let mark = self.out.len();
        let this = std::cell::RefCell::new(self);
        walk::smart(
            py,
            value,
            &union.members,
            label,
            ctx,
            |member| member.py_types.iter().any(|known| known.bind(py).is(&tp)),
            |value, member, ctx| {
                let mut writer = this.borrow_mut();
                if let Err(error) = writer.write(py, value, member, ctx) {
                    writer.out.truncate(mark);
                    return Err(error);
                }
                Ok(value.clone())
            },
        )
        .map(drop)
    }
}

#[cfg(test)]
mod tests {
    use pyo3::prelude::*;
    use pyo3::types::{PyDict, PyString};

    use super::{write_any, write_py_str};

    fn with_python(test: impl for<'py> FnOnce(Python<'py>)) {
        Python::initialize();
        Python::attach(test);
    }

    #[test]
    fn lone_surrogates_are_escaped() {
        with_python(|py| {
            let text = py
                .eval(c"'a\\ud800b\\U0001f600\\udfff'", None, None)
                .unwrap();
            let mut out = Vec::new();
            write_py_str(text.cast::<PyString>().unwrap(), &mut out).unwrap();
            assert_eq!(out, "\"a\\ud800b\u{1f600}\\udfff\"".as_bytes());
        });
    }

    #[test]
    fn converter_output_is_written_generically() {
        with_python(|py| {
            let value = py
                .eval(
                    c"{'a': [1, 2.5, None, True, (2, 'x')], 'b': {}}",
                    None,
                    None,
                )
                .unwrap();
            let mut out = Vec::new();
            assert!(write_any(&value, &mut out, 0).unwrap());
            assert_eq!(out, br#"{"a":[1,2.5,null,true,[2,"x"]],"b":{}}"#);
            for bad in [c"object()", c"{1: 2}", c"[1, {2}]", c"{'a': b'x'}"] {
                let value = py.eval(bad, None, None).unwrap();
                assert!(!write_any(&value, &mut Vec::new(), 0).unwrap(), "{bad:?}");
            }
            let empty = PyDict::new(py);
            let mut out = Vec::new();
            assert!(write_any(empty.as_any(), &mut out, 0).unwrap());
            assert_eq!(out, b"{}");
        });
    }
}
