//! Schema compile: Python `ModelConverter` / converters -> [`Field`] and [`Kind`].

use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyFrozenSet, PySet, PyString, PyTuple, PyType};

use super::kind::{Collect, Field, Kind, Nested};

pub(crate) fn kind(converter: &Bound<'_, PyAny>) -> PyResult<Kind> {
    let py = converter.py();
    let tag: String = converter.getattr(pyo3::intern!(py, "kind"))?.extract()?;
    let flat = || -> PyResult<bool> { converter.getattr(pyo3::intern!(py, "flat"))?.extract() };
    let dict = |name: &str| -> PyResult<Py<PyDict>> {
        Ok(converter.getattr(name)?.cast_into::<PyDict>()?.unbind())
    };
    Ok(match tag.as_str() {
        "str" => Kind::Str,
        "int" => Kind::Int,
        "float" => Kind::Float,
        "bool" => Kind::Bool,
        "optional" => Kind::Optional {
            inner: Box::new(kind(&converter.getattr("inner")?)?),
            flat: flat()?,
        },
        "enum" => {
            let tp = converter.getattr("tp")?;
            Kind::Enum {
                by_value: tp
                    .getattr("_value2member_map_")?
                    .cast_into::<PyDict>()?
                    .unbind(),
                tp: tp.cast_into::<PyType>()?.unbind(),
                by_text: if flat()? {
                    Some(dict("_by_text")?)
                } else {
                    None
                },
            }
        }
        "literal" => Kind::Literal {
            json: converter.getattr("_json")?.unbind(),
            text: if flat()? { Some(dict("_text")?) } else { None },
        },
        "sequence" => Kind::Sequence {
            item: Box::new(kind(&converter.getattr("item")?)?),
            collect: collect(&converter.getattr("tp")?)?,
        },
        "dict" => Kind::Dict(Box::new(kind(&converter.getattr("item")?)?)),
        "model" => Kind::Model(Box::new(Nested {
            converter: converter.clone().unbind(),
            schema: PyOnceLock::new(),
        })),
        _ => Kind::Python(converter.clone().unbind()),
    })
}

fn collect(tp: &Bound<'_, PyAny>) -> PyResult<Collect> {
    let py = tp.py();
    Ok(if tp.is(py.get_type::<PyTuple>()) {
        Collect::Tuple
    } else if tp.is(py.get_type::<PySet>()) {
        Collect::Set
    } else if tp.is(py.get_type::<PyFrozenSet>()) {
        Collect::FrozenSet
    } else {
        Collect::List
    })
}

/// The fields of a `ModelConverter`, plus the interned names of all of them.
pub(crate) fn fields<'py>(
    converter: &Bound<'py, PyAny>,
) -> PyResult<(Vec<Field>, Vec<Bound<'py, PyString>>)> {
    let py = converter.py();
    let missing = py.import("dataclasses")?.getattr("MISSING")?;
    let mut fields = Vec::new();
    let mut names = Vec::new();
    for spec in converter.getattr("fields")?.try_iter()? {
        let spec = spec?;
        let key: String = spec.getattr("name")?.extract()?;
        let default = spec.getattr("default")?;
        let factory = spec.getattr("default_factory")?;
        let name = PyString::intern(py, &key);
        names.push(name.clone());
        fields.push(Field {
            name: name.unbind(),
            key,
            kind: kind(&spec.getattr("converter")?)?,
            default: (!default.is(&missing)).then(|| default.unbind()),
            factory: (!factory.is_none()).then(|| factory.unbind()),
        });
    }
    Ok((fields, names))
}
