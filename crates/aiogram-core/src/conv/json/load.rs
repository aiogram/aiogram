//! The dict load: JSON-shaped Python values (`json.loads` output, any `Mapping`) -> values.

use std::cell::RefCell;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyString, PyTuple};

use crate::conv::construct::{self, Slot};
use crate::conv::errors::{Ctx, Loc, VResult, ValError, expected, field_required, from_user};
use crate::conv::ir::{Collect, Data, Kind, Union};
use crate::conv::model::{self, Build, ModelCore};
use crate::conv::scalars::{self, TextIn};
use crate::conv::walk::{self, Errors, Getter, dict_for_each, json_type_of, type_and_value};

pub(crate) fn load<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let label = kind.label.as_str();
    match &kind.data {
        _ if scalars::is_text_kind(kind) => match value.cast::<PyString>() {
            Ok(text) => scalars::load_text(py, kind, TextIn::Py(text)),
            Err(_) => Err(expected(label, value)),
        },
        Data::Int => scalars::int(value, label),
        Data::Float => scalars::float(value, label),
        Data::Bool => scalars::boolean(value, label),
        Data::Datetime {
            epoch: Some(epoch), ..
        } => scalars::load_epoch(value, *epoch, label),
        Data::Timedelta => scalars::load_timedelta(value, label),
        Data::Decimal { .. } => scalars::load_decimal_number(value, label),
        Data::Text(text) => scalars::parse_text(text, value, label),
        Data::Enum(enumeration) => scalars::load_enum(enumeration, value, label),
        Data::Literal(literal) => {
            scalars::check_literal(literal, value, label).map(|()| value.clone())
        }
        Data::Optional(inner) => {
            if value.is_none() {
                Ok(value.clone())
            } else {
                load(py, value, inner.get(), ctx)
            }
        }
        Data::Sequence { item, collect } => sequence(py, value, item.get(), *collect, label, ctx),
        Data::Tuple(items) => tuple(py, value, items, label, ctx),
        Data::Dict(item) => dict(py, value, item.get(), label, ctx),
        Data::Model(core) => {
            let core = core
                .get()
                .ok_or_else(|| PyRuntimeError::new_err("model kind cleared"))?;
            self::model(py, value, core.get(), label, ctx)
        }
        Data::Union(union) => self::union(py, value, union, label, ctx),
        Data::Python { converter, .. } => converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "from_json"), (value,))
            .map_err(|error| from_user(py, error, value)),
        Data::Lazy(_) => load(py, value, kind.resolved(py)?, ctx.deeper()?),
        Data::Str
        | Data::Uuid { .. }
        | Data::Datetime { .. }
        | Data::Date
        | Data::Time { .. }
        | Data::Bytes => Err(ValError::Fatal(PyRuntimeError::new_err(
            "unreachable text kind",
        ))),
    }
}

/// A `list` of loaded items as the sequence's container.
pub(crate) fn collect<'py>(
    py: Python<'py>,
    items: Vec<Bound<'py, PyAny>>,
    collect: Collect,
) -> PyResult<Bound<'py, PyAny>> {
    Ok(match collect {
        Collect::List => PyList::new(py, items)?.into_any(),
        Collect::Tuple => PyTuple::new(py, items)?.into_any(),
        Collect::Set => PySet::new(py, &items)?.into_any(),
        Collect::FrozenSet => PyFrozenSet::new(py, &items)?.into_any(),
    })
}

/// Load each item of a `list` / `tuple` with `each(index, item)`; `None` when `value` is neither.
fn items<'py>(
    value: &Bound<'py, PyAny>,
    mut each: impl FnMut(usize, Bound<'py, PyAny>) -> VResult<()>,
) -> Option<VResult<()>> {
    if let Ok(list) = value.cast::<PyList>() {
        Some(
            list.iter()
                .enumerate()
                .try_for_each(|(index, item)| each(index, item)),
        )
    } else if let Ok(tuple) = value.cast::<PyTuple>() {
        Some(
            tuple
                .iter()
                .enumerate()
                .try_for_each(|(index, item)| each(index, item)),
        )
    } else {
        None
    }
}

fn sequence<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    item: &Kind,
    container: Collect,
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let ctx = ctx.deeper()?;
    let mut out = Vec::new();
    let mut errors = Errors::new();
    let walked = items(value, |index, element| {
        match load(py, &element, item, ctx) {
            Ok(loaded) => out.push(loaded),
            Err(error) => errors.push(error.at_index(index), ctx)?,
        }
        Ok(())
    });
    walked.ok_or_else(|| expected(label, value))??;
    errors.finish()?;
    Ok(collect(py, out, container)?)
}

fn tuple<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kinds: &[Py<Kind>],
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let ctx = ctx.deeper()?;
    let length = if let Ok(list) = value.cast::<PyList>() {
        list.len()
    } else if let Ok(tuple) = value.cast::<PyTuple>() {
        tuple.len()
    } else {
        return Err(expected(label, value));
    };
    if length != kinds.len() {
        return Err(ValError::new(
            format!("expected {} items", kinds.len()),
            Some(value),
        ));
    }
    let mut out = Vec::with_capacity(length);
    let mut errors = Errors::new();
    let walked = items(value, |index, element| {
        let kind = kinds
            .get(index)
            .ok_or_else(|| PyRuntimeError::new_err("tuple changed size"))?;
        match load(py, &element, kind.get(), ctx) {
            Ok(loaded) => out.push(loaded),
            Err(error) => errors.push(error.at_index(index), ctx)?,
        }
        Ok(())
    });
    walked.ok_or_else(|| expected(label, value))??;
    errors.finish()?;
    Ok(PyTuple::new(py, out)?.into_any())
}

/// `expected str key` at the key's `repr`, with the key as value.
pub(crate) fn str_key_error(key: &Bound<'_, PyAny>) -> VResult<ValError> {
    let repr = key.repr()?.unbind();
    let py = key.py();
    Ok(ValError::new("expected str key", Some(key)).at(|| Loc::Key(repr.clone_ref(py))))
}

fn dict<'py>(
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
        match load(py, &element, item, ctx) {
            Ok(loaded) => Ok(out.set_item(name, loaded)?),
            Err(error) => errors
                .borrow_mut()
                .push(error.at(|| Loc::Key(name.clone().unbind())), ctx),
        }
    })?;
    errors.into_inner().finish()?;
    Ok(out.into_any())
}

/// The value of `field` in `getter`: its stored key, then each `load` key.
fn lookup<'py>(
    getter: &Getter<'py>,
    field: &crate::conv::ir::Field,
    py: Python<'py>,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    if let Some(value) = getter.get(field.key.bind(py))? {
        return Ok(Some(value));
    }
    for key in &field.load {
        if let Some(value) = getter.get(key.bind(py))? {
            return Ok(Some(value));
        }
    }
    Ok(None)
}

/// Fill a missing field: its default or factory, `field required`, or (TypedDict, not required)
/// nothing.
pub(crate) fn missing<'py>(
    py: Python<'py>,
    core: &ModelCore,
    field: &crate::conv::ir::Field,
    errors: &mut Errors,
    ctx: Ctx,
) -> VResult<Slot<'py>> {
    if core.build == Build::Dict {
        if field.required {
            errors.push(field_required(py, &field.key), ctx)?;
        }
        return Ok((None, false));
    }
    match construct::default(py, field)? {
        Some(value) => Ok((Some(value), false)),
        None => {
            errors.push(field_required(py, &field.key), ctx)?;
            Ok((None, false))
        }
    }
}

pub(crate) fn model<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    core: &ModelCore,
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    let ctx = ctx.deeper()?;
    let fields = core.fields(py)?;
    let getter = Getter::new(value)?.ok_or_else(|| expected(label, value))?;
    let mut slots = Vec::with_capacity(fields.list.len());
    let mut errors = Errors::new();
    for field in &fields.list {
        let field = field.get();
        match lookup(&getter, field, py)? {
            Some(raw) => match load(py, &raw, field.kind.get(), ctx) {
                Ok(loaded) => slots.push((Some(loaded), true)),
                Err(error) => {
                    errors.push(error.at_key(py, &field.key), ctx)?;
                    slots.push((None, true));
                }
            },
            None => slots.push(missing(py, core, field, &mut errors, ctx)?),
        }
    }
    errors.finish()?;
    construct::build(py, core, fields, slots, &|| Ok(value.clone()))
}

pub(crate) fn union<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    union: &Union,
    label: &str,
    ctx: Ctx,
) -> VResult<Bound<'py, PyAny>> {
    if union.nullable && value.is_none() {
        return Ok(value.clone());
    }
    if union.discriminator.is_some() {
        let member = discriminated(py, union, label, value)?;
        return load(py, value, member, ctx);
    }
    let json_type = json_type_of(value)?;
    walk::smart(
        py,
        value,
        &union.members,
        label,
        ctx,
        |member| member.json_types & json_type != 0,
        |value, member, ctx| load(py, value, member, ctx),
    )
}

/// The member a discriminated union's tag selects: the tag is read at its stored key, then at
/// its fallback `load` keys (data stored before a rename).
pub(crate) fn discriminated<'a>(
    py: Python<'_>,
    union: &'a Union,
    label: &str,
    value: &Bound<'_, PyAny>,
) -> VResult<&'a Kind> {
    let tags = model::union_tags(py, union, label)?;
    let getter = Getter::new(value)?.ok_or_else(|| expected(label, value))?;
    let mut found = None;
    for key in std::iter::once(&tags.key).chain(&tags.load) {
        if let Some(tag) = getter.get(key.bind(py))? {
            found = Some((key, tag));
            break;
        }
    }
    let Some((key, tag)) = found else {
        return Err(field_required(py, &tags.key));
    };
    let index = match tags.by_tag.bind(py).get_item(type_and_value(&tag)?) {
        Ok(Some(index)) => index.extract::<usize>()?,
        _ => return Err(expected(&tags.label, &tag).at_key(py, key)),
    };
    Ok(union
        .members
        .get(index)
        .ok_or_else(|| PyRuntimeError::new_err("discriminator tag out of range"))?
        .get())
}
