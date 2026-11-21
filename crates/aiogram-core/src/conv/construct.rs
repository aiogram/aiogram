//! Building instances (every load path) and `ModelBase.__init__` (`ModelCore.init`).

use pyo3::exceptions::{PyRuntimeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyString, PyTuple};

use super::check;
use super::errors::{Ctx, VResult, ValError, from_user, materialize};
use super::ir::Field;
use super::model::{Build, Fields, ModelCore};
use super::scalars::{new_instance, set_attr};
use super::walk::Errors;

/// One field's value while loading, and whether its key (or a `load` key) was present.
pub(crate) type Slot<'py> = (Option<Bound<'py, PyAny>>, bool);

/// The default of a missing field (shared), its factory's result, or `None`.
pub(crate) fn default<'py>(py: Python<'py>, field: &Field) -> PyResult<Option<Bound<'py, PyAny>>> {
    if let Some(default) = &field.default {
        return Ok(Some(default.bind(py).clone()));
    }
    field
        .factory
        .as_ref()
        .map(|factory| factory.bind(py).call0())
        .transpose()
}

/// The index of the field whose attribute name is `name`.
pub(crate) fn field_index(fields: &Fields, name: &Bound<'_, PyString>) -> PyResult<Option<usize>> {
    let py = name.py();
    if let Some(index) = fields
        .list
        .iter()
        .position(|field| field.get().name.bind(py).is(name))
    {
        return Ok(Some(index)); // interned names: the usual case
    }
    for (index, field) in fields.list.iter().enumerate() {
        if field.get().name.bind(py).as_any().eq(name)? {
            return Ok(Some(index));
        }
    }
    Ok(None)
}

fn unset(core: &ModelCore, field: &Field, py: Python<'_>) -> PyErr {
    PyRuntimeError::new_err(format!(
        "{}.{} has no value",
        core.qualname,
        field.name.bind(py)
    ))
}

/// Build the instance of `core` from loaded slots; `input` gives the loaded mapping, the value of
/// a `__post_init__` / constructor error.
pub(crate) fn build<'py>(
    py: Python<'py>,
    core: &ModelCore,
    fields: &Fields,
    slots: Vec<Slot<'py>>,
    input: &dyn Fn() -> PyResult<Bound<'py, PyAny>>,
) -> VResult<Bound<'py, PyAny>> {
    let tp = core.tp.bind(py);
    match core.build {
        Build::Dict => {
            let out = PyDict::new(py);
            for (field, (value, _)) in fields.list.iter().zip(slots) {
                if let Some(value) = value {
                    out.set_item(&field.get().name, value)?;
                }
            }
            Ok(out.into_any())
        }
        Build::Call => {
            let kwargs = PyDict::new(py);
            for (field, (value, _)) in fields.list.iter().zip(slots) {
                let field = field.get();
                kwargs.set_item(&field.name, value.ok_or_else(|| unset(core, field, py))?)?;
            }
            tp.call((), Some(&kwargs))
                .map_err(|error| user_error(py, error, input))
        }
        Build::Model => {
            let instance = new_instance(tp)?;
            let mut names = Vec::new();
            let all = slots.iter().all(|(_, present)| *present);
            for (field, (value, present)) in fields.list.iter().zip(slots) {
                let field = field.get();
                let name = field.name.bind(py);
                set_attr(
                    &instance,
                    name,
                    &value.ok_or_else(|| unset(core, field, py))?,
                )?;
                if present && !all {
                    names.push(name.clone());
                }
            }
            finish(py, fields, &instance, all, &names)?;
            if core.post_init {
                instance
                    .call_method0(pyo3::intern!(py, "__post_init__"))
                    .map_err(|error| user_error(py, error, input))?;
            }
            Ok(instance)
        }
    }
}

fn user_error<'py>(
    py: Python<'py>,
    error: PyErr,
    input: &dyn Fn() -> PyResult<Bound<'py, PyAny>>,
) -> ValError {
    match input() {
        Ok(input) => from_user(py, error, &input),
        Err(failure) => ValError::Fatal(failure),
    }
}

/// Set `__fields_set__`: the shared `all_set`, or a frozenset of `names`.
fn finish(
    py: Python<'_>,
    fields: &Fields,
    instance: &Bound<'_, PyAny>,
    all: bool,
    names: &[Bound<'_, PyString>],
) -> PyResult<()> {
    let fields_set = if all {
        fields.all_set.bind(py).clone()
    } else {
        PyFrozenSet::new(py, names)?
    };
    set_attr(
        instance,
        pyo3::intern!(py, "__fields_set__"),
        &fields_set.into_any(),
    )
}

fn plural(count: usize, word: &str) -> String {
    if count == 1 {
        format!("{count} {word}")
    } else {
        format!("{count} {word}s")
    }
}

/// `'a'`, `'a' and 'b'`, `'a', 'b', and 'c'` (as CPython words missing arguments).
fn names_list(names: &[String]) -> String {
    match names {
        [] => String::new(),
        [one] => one.clone(),
        [first, second] => format!("{first} and {second}"),
        [rest @ .., last] => format!("{}, and {last}", rest.join(", ")),
    }
}

/// `ModelBase.__init__`: bind the arguments as dataclasses do, check every given value (errors
/// collected, raised as `ConversionError("constructing <qualname>")`), fill the defaults, set the
/// attributes and `__fields_set__`, run `__post_init__`.
pub(crate) fn init(
    py: Python<'_>,
    core: &ModelCore,
    instance: &Bound<'_, PyAny>,
    args: &Bound<'_, PyTuple>,
    kwargs: &Bound<'_, PyAny>,
) -> PyResult<()> {
    let fields = core.fields(py)?;
    let qualname = &core.qualname;
    let mut given: Vec<Option<Bound<'_, PyAny>>> = fields.list.iter().map(|_| None).collect();
    for (&index, arg) in fields.positional.iter().zip(args.iter()) {
        given[index] = Some(arg);
    }
    if !kwargs.is_none() {
        for (key, value) in kwargs.cast::<PyDict>()?.iter() {
            let key = key.cast_into::<PyString>().map_err(|_| {
                PyTypeError::new_err(format!("{qualname}.__init__() keywords must be strings"))
            })?;
            let index = field_index(fields, &key)?.filter(|&index| fields.list[index].get().init);
            let Some(index) = index else {
                return Err(PyTypeError::new_err(format!(
                    "{qualname}.__init__() got an unexpected keyword argument {}",
                    key.repr()?
                )));
            };
            if given[index].is_some() {
                return Err(PyTypeError::new_err(format!(
                    "{qualname}.__init__() got multiple values for argument {}",
                    key.repr()?
                )));
            }
            given[index] = Some(value);
        }
    }
    if args.len() > fields.positional.len() {
        let takes = fields.positional.len() + 1; // with `self`, as CPython counts
        let got = args.len() + 1;
        return Err(PyTypeError::new_err(format!(
            "{qualname}.__init__() takes {} but {got} {} given",
            plural(takes, "positional argument"),
            if got == 1 { "was" } else { "were" }
        )));
    }
    let mut missing_positional = Vec::new();
    let mut missing_keyword = Vec::new();
    for (field, value) in fields.list.iter().zip(&given) {
        let field = field.get();
        if field.init && value.is_none() && !field.has_default() {
            let name = field.name.bind(py).repr()?.to_string();
            if field.kw_only {
                missing_keyword.push(name);
            } else {
                missing_positional.push(name);
            }
        }
    }
    for (missing, what) in [
        (missing_positional, "positional"),
        (missing_keyword, "keyword-only"),
    ] {
        if !missing.is_empty() {
            return Err(PyTypeError::new_err(format!(
                "{qualname}.__init__() missing {}: {}",
                plural(missing.len(), &format!("required {what} argument")),
                names_list(&missing)
            )));
        }
    }

    let fail = |error: ValError| materialize(py, &format!("constructing {qualname}"), error);
    let ctx = Ctx::new(false).deeper().map_err(fail)?;
    let mut errors = Errors::new();
    for (field, value) in fields.list.iter().zip(&given) {
        let field = field.get();
        if let Some(value) = value
            && let Err(error) = check::check(py, value, field.kind.get(), ctx)
            && let Err(stop) = errors.push(error.at_key(py, &field.key), ctx)
        {
            return Err(fail(stop));
        }
    }
    errors.finish().map_err(fail)?;

    let mut names = Vec::new();
    let all = given.iter().all(Option::is_some);
    for (field, value) in fields.list.iter().zip(given) {
        let field = field.get();
        let name = field.name.bind(py);
        let value = match value {
            Some(value) => {
                if !all {
                    names.push(name.clone());
                }
                value
            }
            None => default(py, field)?.ok_or_else(|| unset(core, field, py))?,
        };
        set_attr(instance, name, &value)?;
    }
    finish(py, fields, instance, all, &names)?;
    if core.post_init {
        instance.call_method0(pyo3::intern!(py, "__post_init__"))?;
    }
    Ok(())
}
