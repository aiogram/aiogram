//! The dict dump: Python values -> JSON-shaped Python values, strictly. With `BUILD = false` the
//! same walk only checks the values ([`crate::conv::check`]).

use std::cell::RefCell;

use pyo3::exceptions::{PyAttributeError, PyRecursionError, PyRuntimeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};

use crate::conv::construct::field_index;
use crate::conv::errors::{
    Ctx, Loc, MAX_DEPTH, VResult, ValError, expected, field_required, from_user,
};
use crate::conv::ir::{Data, Kind, Union};
use crate::conv::json::load::str_key_error;
use crate::conv::model::{Build, ModelCore};
use crate::conv::scalars;
use crate::conv::walk::{self, Errors, dict_for_each};

pub(crate) fn dump<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    walk::<true>(py, value, kind, ctx)
}

/// One value: its JSON-shaped dump (`BUILD`), or the value itself once checked.
pub(crate) fn walk<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let label = kind.label.as_str();
    match &kind.data {
        Data::Optional(inner) => {
            if value.is_none() {
                Ok(value.clone())
            } else {
                walk::<BUILD>(py, value, inner.get(), ctx)
            }
        }
        Data::Sequence { item, .. } => sequence::<BUILD>(py, value, kind, item.get(), ctx),
        Data::Tuple(kinds) => tuple::<BUILD>(py, value, kinds, label, ctx),
        Data::Dict(item) => dict::<BUILD>(py, value, item.get(), label, ctx),
        Data::Model(core) => {
            let core = core
                .get()
                .ok_or_else(|| PyRuntimeError::new_err("model kind cleared"))?;
            let out = model::<BUILD>(py, value, core.get(), label, ctx)?;
            Ok(if BUILD { out.into_any() } else { value.clone() })
        }
        Data::Union(union) => self::union::<BUILD>(py, value, union, label, ctx),
        Data::Lazy(_) => walk::<BUILD>(py, value, kind.resolved(py)?, ctx),
        _ => scalar::<BUILD>(py, value, kind),
    }
}

/// The non-recursive kinds of [`walk`], out of line so the recursive frame stays small.
#[inline(never)]
fn scalar<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
) -> VResult<Bound<'py, PyAny>> {
    let label = kind.label.as_str();
    match &kind.data {
        Data::Str => {
            if value.is_instance_of::<PyString>() {
                Ok(value.clone())
            } else {
                Err(expected(label, value))
            }
        }
        Data::Int => {
            if BUILD {
                scalars::int(value, label)
            } else if value.is_instance_of::<PyInt>() && !value.is_instance_of::<PyBool>() {
                Ok(value.clone())
            } else {
                Err(expected(label, value))
            }
        }
        Data::Float => scalars::float(value, label),
        Data::Bool => scalars::boolean(value, label),
        Data::Datetime {
            epoch: Some(epoch), ..
        } => {
            let number = scalars::dump_epoch(value, *epoch, label)?;
            Ok(if BUILD {
                number.object(py)
            } else {
                value.clone()
            })
        }
        Data::Timedelta => {
            let number = scalars::dump_timedelta(value, label)?;
            Ok(if BUILD {
                number.object(py)
            } else {
                value.clone()
            })
        }
        Data::Decimal { number: true } => {
            scalars::finite_decimal(value, label)?;
            Ok(if BUILD {
                py.get_type::<PyFloat>().call1((value,))?
            } else {
                value.clone()
            })
        }
        _ if scalars::is_text_kind(kind) => {
            let mut text = String::new();
            scalars::dump_text(py, value, kind, &mut text)?;
            Ok(if BUILD {
                PyString::new(py, &text).into_any()
            } else {
                value.clone()
            })
        }
        Data::Text(text) => {
            let formatted = scalars::format_text(text, value, label)?;
            Ok(if BUILD {
                formatted.into_any()
            } else {
                value.clone()
            })
        }
        Data::Enum(enumeration) => {
            let dumped = scalars::dump_enum(enumeration, value, label)?;
            Ok(if BUILD { dumped } else { value.clone() })
        }
        Data::Literal(literal) => {
            scalars::check_literal(literal, value, label).map(|()| value.clone())
        }
        Data::Python { converter, .. } => {
            let result = to_json(py, converter, value)?;
            if !json_shaped(&result, 0)? {
                return Err(non_json(label, &result));
            }
            Ok(if BUILD { result } else { value.clone() })
        }
        _ => Err(ValError::Fatal(PyRuntimeError::new_err(
            "not a scalar kind",
        ))),
    }
}

#[inline(never)] // keeps the recursive `walk` frame small (the depth guard counts on it)
fn sequence<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
    item: &Kind,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let label = kind.label.as_str();
    let container = kind
        .py_types
        .first()
        .ok_or_else(|| PyRuntimeError::new_err("sequence without a type"))?;
    if !value.is_instance(container.bind(py))? {
        return Err(expected(label, value));
    }
    let ctx = ctx.deeper()?;
    let mut out = Vec::new();
    let mut errors = Errors::new();
    for (index, element) in value.try_iter()?.enumerate() {
        match walk::<BUILD>(py, &element?, item, ctx) {
            Ok(dumped) if BUILD => out.push(dumped),
            Ok(_) => {}
            Err(error) => errors.push(error.at_index(index), ctx)?,
        }
    }
    errors.finish()?;
    Ok(if BUILD {
        PyList::new(py, out)?.into_any()
    } else {
        value.clone()
    })
}

#[inline(never)] // keeps the recursive `walk` frame small (the depth guard counts on it)
fn tuple<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kinds: &[Py<Kind>],
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
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
    let mut out = Vec::new();
    let mut errors = Errors::new();
    for (index, (element, item)) in tuple.iter().zip(kinds).enumerate() {
        match walk::<BUILD>(py, &element, item.get(), ctx) {
            Ok(dumped) if BUILD => out.push(dumped),
            Ok(_) => {}
            Err(error) => errors.push(error.at_index(index), ctx)?,
        }
    }
    errors.finish()?;
    Ok(if BUILD {
        PyList::new(py, out)?.into_any()
    } else {
        value.clone()
    })
}

#[inline(never)] // keeps the recursive `walk` frame small (the depth guard counts on it)
fn dict<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    item: &Kind,
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let source = value.cast::<PyDict>().map_err(|_| expected(label, value))?;
    let ctx = ctx.deeper()?;
    let out = PyDict::new(py);
    let errors = RefCell::new(Errors::new());
    dict_for_each(source, |key, element| {
        let Ok(name) = key.cast::<PyString>() else {
            return errors.borrow_mut().push(str_key_error(&key)?, ctx);
        };
        match walk::<BUILD>(py, &element, item, ctx) {
            Ok(dumped) => {
                if BUILD {
                    out.set_item(name, dumped)?;
                }
                Ok(())
            }
            Err(error) => errors
                .borrow_mut()
                .push(error.at(|| Loc::Key(name.clone().unbind())), ctx),
        }
    })?;
    errors.into_inner().finish()?;
    Ok(if BUILD { out.into_any() } else { value.clone() })
}

/// A user converter's `to_json(value)`.
pub(crate) fn to_json<'py>(
    py: Python<'py>,
    converter: &Py<PyAny>,
    value: &Bound<'py, PyAny>,
) -> VResult<Bound<'py, PyAny>> {
    converter
        .bind(py)
        .call_method1(pyo3::intern!(py, "to_json"), (value,))
        .map_err(|error| from_user(py, error, value))
}

pub(crate) fn non_json(label: &str, value: &Bound<'_, PyAny>) -> ValError {
    ValError::new(
        format!("{label}.to_json returned a non-JSON value"),
        Some(value),
    )
}

/// Whether `value` is JSON-shaped: scalars, `list` / `tuple`, `dict` with `str` keys.
fn json_shaped(value: &Bound<'_, PyAny>, depth: u32) -> PyResult<bool> {
    if depth > MAX_DEPTH {
        return Err(PyRecursionError::new_err(
            "maximum nesting depth exceeded while converting",
        ));
    }
    if value.is_none()
        || value.is_instance_of::<PyString>()
        || value.is_instance_of::<PyInt>()
        || value.is_instance_of::<PyFloat>()
    {
        return Ok(true);
    }
    if let Ok(list) = value.cast::<PyList>() {
        for item in list.iter() {
            if !json_shaped(&item, depth + 1)? {
                return Ok(false);
            }
        }
        return Ok(true);
    }
    if let Ok(tuple) = value.cast::<PyTuple>() {
        for item in tuple.iter() {
            if !json_shaped(&item, depth + 1)? {
                return Ok(false);
            }
        }
        return Ok(true);
    }
    if let Ok(dict) = value.cast::<PyDict>() {
        let shaped = std::cell::Cell::new(true);
        let result = dict_for_each(dict, |key, item| {
            if !key.is_instance_of::<PyString>() || !json_shaped(&item, depth + 1)? {
                shaped.set(false);
                return Err(ValError::Lines(Vec::new())); // stop
            }
            Ok(())
        });
        return match result {
            Err(ValError::Fatal(error)) => Err(error),
            _ => Ok(shaped.get()),
        };
    }
    Ok(false)
}

/// `obj.__fields_set__` when `exclude_unset` applies; `None`: dump every field.
pub(crate) fn fields_set<'py>(
    core: &ModelCore,
    value: &Bound<'py, PyAny>,
    ctx: Ctx,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    if !ctx.exclude_unset || core.build == Build::Dict {
        return Ok(None);
    }
    match value.getattr(pyo3::intern!(value.py(), "__fields_set__")) {
        Ok(set) => Ok(Some(set)),
        Err(error) if error.is_instance_of::<PyAttributeError>(value.py()) => Ok(None),
        Err(error) => Err(error),
    }
}

fn model<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    core: &ModelCore,
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyDict>> {
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
    let out = PyDict::new(py);
    let mut errors = Errors::new();
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
        match walk::<BUILD>(py, &attribute, field.kind.get(), ctx) {
            Ok(dumped) => {
                if BUILD {
                    out.set_item(&field.key, dumped)?;
                }
            }
            Err(error) => errors.push(error.at_key(py, &field.key), ctx)?,
        }
    }
    errors.finish()?;
    Ok(out)
}

fn union<'py, const BUILD: bool>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    union: &Union,
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    if union.nullable && value.is_none() {
        return Ok(value.clone());
    }
    let tp = value.get_type();
    walk::smart(
        py,
        value,
        &union.members,
        label,
        ctx,
        |member| member.py_types.iter().any(|known| known.bind(py).is(&tp)),
        |value, member, ctx| walk::<BUILD>(py, value, member, ctx),
    )
}

/// `JsonSchema.dump_fields`: attribute name -> value in, stored key -> dump out.
pub(crate) fn dump_fields<'py>(
    py: Python<'py>,
    core: &ModelCore,
    values: &Bound<'py, PyAny>,
) -> VResult<Bound<'py, PyDict>> {
    let fields = core.fields(py)?;
    let ctx = Ctx::new(false).deeper()?;
    let out = PyDict::new(py);
    let errors = RefCell::new(Errors::new());
    let each = |name: Bound<'py, PyAny>, value: Bound<'py, PyAny>| -> VResult<()> {
        let index = match name.cast::<PyString>() {
            Ok(name) => field_index(fields, name)?,
            Err(_) => None,
        };
        let Some(index) = index else {
            return Err(ValError::Fatal(PyTypeError::new_err(format!(
                "{} has no field {}",
                core.qualname,
                name.repr()?
            ))));
        };
        let field = fields.list[index].get();
        match dump(py, &value, field.kind.get(), ctx) {
            Ok(dumped) => Ok(out.set_item(&field.key, dumped)?),
            Err(error) => errors.borrow_mut().push(error.at_key(py, &field.key), ctx),
        }
    };
    if let Ok(dict) = values.cast_exact::<PyDict>() {
        dict_for_each(dict, each)?;
    } else {
        for item in values
            .call_method0(pyo3::intern!(py, "items"))?
            .try_iter()?
        {
            let (name, value): (Bound<'py, PyAny>, Bound<'py, PyAny>) = item?.extract()?;
            each(name, value)?;
        }
    }
    errors.into_inner().finish()?;
    Ok(out)
}
