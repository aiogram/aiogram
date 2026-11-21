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

#[cfg(test)]
mod tests {
    use pyo3::prelude::*;
    use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet};

    use super::load;
    use crate::conv::kind::{Collect, Kind};

    fn with_python(test: impl for<'py> FnOnce(Python<'py>)) {
        Python::initialize();
        Python::attach(test);
    }

    #[test]
    fn exact_scalars_pass_through_and_others_fall_back() {
        with_python(|py| {
            let one = 1i64.into_pyobject(py).unwrap().into_any();
            assert!(load(py, &one, &Kind::Int).unwrap().is(&one));
            let float = load(py, &one, &Kind::Float).unwrap();
            assert_eq!(float.extract::<f64>().unwrap(), 1.0);
            let flag = true.into_pyobject(py).unwrap().to_owned().into_any();
            assert!(
                load(py, &flag, &Kind::Int).is_err(),
                "bool is not an int field"
            );
            let text = "x".into_pyobject(py).unwrap().into_any();
            assert!(load(py, &text, &Kind::Float).is_err());
        });
    }

    #[test]
    fn sequences_build_their_container() {
        with_python(|py| {
            let items = PyList::new(py, [1i64, 2, 2]).unwrap().into_any();
            let int = || Box::new(Kind::Int);
            let set = load(
                py,
                &items,
                &Kind::Sequence {
                    item: int(),
                    collect: Collect::Set,
                },
            )
            .unwrap();
            assert!(set.is_instance_of::<PySet>());
            assert_eq!(set.len().unwrap(), 2);
            let frozen = load(
                py,
                &items,
                &Kind::Sequence {
                    item: int(),
                    collect: Collect::FrozenSet,
                },
            )
            .unwrap();
            assert!(frozen.is_instance_of::<PyFrozenSet>());
            let mixed = PyList::new(
                py,
                [
                    1i64.into_pyobject(py).unwrap().into_any(),
                    "x".into_pyobject(py).unwrap().into_any(),
                ],
            )
            .unwrap()
            .into_any();
            assert!(
                load(
                    py,
                    &mixed,
                    &Kind::Sequence {
                        item: int(),
                        collect: Collect::List
                    }
                )
                .is_err()
            );
        });
    }

    #[test]
    fn dicts_need_string_keys() {
        with_python(|py| {
            let good = PyDict::new(py);
            good.set_item("a", 1i64).unwrap();
            let loaded = load(py, good.as_any(), &Kind::Dict(Box::new(Kind::Float))).unwrap();
            let value: f64 = loaded.get_item("a").unwrap().extract().unwrap();
            assert_eq!(value, 1.0);
            let bad = PyDict::new(py);
            bad.set_item(1i64, 1i64).unwrap();
            assert!(load(py, bad.as_any(), &Kind::Dict(Box::new(Kind::Int))).is_err());
        });
    }
}
