//! Dict walker: JSON-shaped Python values -> instance (`ModelConverter.from_json`).
//!
//! Mirrors each Python `from_json` on the inputs it accepts as they are. Any other input
//! (subclasses, coercions, rejected values) falls back.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};

use super::fallback::{Fallback, Fast};
use super::kind::Kind;
use super::schema::ModelSchema;

pub(crate) fn load_model<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    schema: &ModelSchema,
) -> Fast<Bound<'py, PyAny>> {
    // Python takes any Mapping; the fast path takes exact dicts.
    let dict = value.cast_exact::<PyDict>().map_err(|_| Fallback)?;
    let mut values = Vec::with_capacity(schema.fields.len());
    for field in &schema.fields {
        values.push(match dict.get_item(field.name.bind(py))? {
            Some(item) => Some(load(py, &item, &field.kind)?),
            None => None,
        });
    }
    schema.build(py, values)
}

pub(crate) fn load<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
) -> Fast<Bound<'py, PyAny>> {
    match kind {
        Kind::Str if value.is_instance_of::<PyString>() => Ok(value.clone()),
        Kind::Int if value.is_exact_instance_of::<PyInt>() => Ok(value.clone()),
        Kind::Float if value.is_exact_instance_of::<PyFloat>() => Ok(value.clone()),
        Kind::Float if value.is_exact_instance_of::<PyInt>() => {
            // float(int); outside i64 Python's rounding applies, so fall back
            let int: i64 = value.extract()?;
            #[allow(clippy::cast_precision_loss)] // the same round-to-nearest as float(int)
            Ok(PyFloat::new(py, int as f64).into_any())
        }
        Kind::Bool if value.is_exact_instance_of::<PyBool>() => Ok(value.clone()),
        Kind::Optional { .. } if value.is_none() => Ok(value.clone()),
        Kind::Optional { inner, .. } => load(py, value, inner),
        Kind::Enum { by_value, .. } => by_value.bind(py).get_item(value)?.ok_or(Fallback),
        Kind::Literal { json, .. } => {
            let key = PyTuple::new(py, [value.get_type().into_any(), value.clone()])?;
            match json.bind(py).contains(key)? {
                true => Ok(value.clone()),
                false => Err(Fallback),
            }
        }
        Kind::Sequence { item, collect } => {
            let out = PyList::empty(py);
            if let Ok(list) = value.cast_exact::<PyList>() {
                for element in list.iter() {
                    out.append(load(py, &element, item)?)?;
                }
            } else if let Ok(source) = value.cast_exact::<PyTuple>() {
                for element in source.iter() {
                    out.append(load(py, &element, item)?)?;
                }
            } else {
                return Err(Fallback);
            }
            Ok(collect.finish(out)?)
        }
        Kind::Dict(item) => {
            let source = value.cast_exact::<PyDict>().map_err(|_| Fallback)?;
            let out = PyDict::new(py);
            // a critical section on free-threaded builds, so no concurrent resize mid-walk;
            // an error stops the walk and becomes the fallback
            source.locked_for_each(|key, element| {
                if !key.is_instance_of::<PyString>() {
                    return Err(PyValueError::new_err("fallback"));
                }
                let converted = load(py, &element, item)
                    .map_err(|Fallback| PyValueError::new_err("fallback"))?;
                out.set_item(key, converted)
            })?;
            Ok(out.into_any())
        }
        Kind::Model(nested) => {
            let schema = nested.schema(py)?;
            load_model(py, value, schema.get())
        }
        Kind::Python(converter) => Ok(converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "from_json"), (value,))?),
        _ => Err(Fallback),
    }
}
