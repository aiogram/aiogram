//! Schema compile: Python converters -> [`Kind`] and [`Field`].

use pyo3::prelude::*;
use std::sync::OnceLock;

use pyo3::types::{PyDict, PyFrozenSet, PySet, PyString, PyTuple, PyType};

use super::errors;
use super::kind::{
    Collect, Data, Discriminator, Enumeration, Field, Kind, Literal, Member, Nested, Text,
    TypedDict, TypedDictField, Union,
};

/// Compile `converter`. A field converter (`native = false`) is mirrored only when its class
/// declares `kind` itself; a subclass that inherits it may override the methods, so it is called
/// instead. A built-in's own core (`native = true`) always uses its declared kind.
pub(crate) fn kind(converter: &Bound<'_, PyAny>, native: bool) -> PyResult<Kind> {
    let py = converter.py();
    let own = native
        || converter
            .get_type()
            .getattr(pyo3::intern!(py, "__dict__"))?
            .contains(pyo3::intern!(py, "kind"))?;
    let tag: String = if own {
        converter.getattr(pyo3::intern!(py, "kind"))?.extract()?
    } else {
        String::from("python")
    };
    let flat = || -> PyResult<bool> { converter.getattr(pyo3::intern!(py, "flat"))?.extract() };
    let attr = |name: &str| converter.getattr(name);
    let dict =
        |name: &str| -> PyResult<Py<PyDict>> { Ok(attr(name)?.cast_into::<PyDict>()?.unbind()) };
    let name_of = |tp: &Bound<'_, PyAny>| -> PyResult<String> { tp.getattr("__name__")?.extract() };
    let data = match tag.as_str() {
        "str" => Data::Str,
        "int" => Data::Int,
        "float" => Data::Float,
        "bool" => Data::Bool,
        "text" => {
            let tp = attr("tp")?;
            let reject = attr("reject")?;
            Data::Text(Box::new(Text {
                name: name_of(&tp)?,
                tp: tp.cast_into::<PyType>()?.unbind(),
                reject: if reject.is_none() {
                    None
                } else {
                    Some(reject.cast_into::<PyType>()?.unbind())
                },
                parse: attr("parse")?.unbind(),
                to_text: attr("to_text")?.unbind(),
                to_flat: attr("to_flat")?.unbind(),
                flat: flat()?,
            }))
        }
        "enum" => {
            let tp = attr("tp")?;
            Data::Enum(Box::new(Enumeration {
                name: name_of(&tp)?,
                by_json: dict("_by_json")?,
                tp: tp.cast_into::<PyType>()?.unbind(),
                by_text: if flat()? {
                    Some(dict("_by_text")?)
                } else {
                    None
                },
            }))
        }
        "literal" => Data::Literal(Box::new(Literal {
            json: attr("_json")?.unbind(),
            text: if flat()? { Some(dict("_text")?) } else { None },
            label: attr("label")?.extract()?,
        })),
        "optional" => Data::Optional {
            inner: Box::new(kind(&attr("inner")?, false)?),
            flat: flat()?,
        },
        "sequence" => {
            let tp = attr("tp")?;
            Data::Sequence {
                item: Box::new(kind(&attr("item")?, false)?),
                collect: collect(&tp)?,
                tp: tp.cast_into::<PyType>()?.unbind(),
            }
        }
        "dict" => Data::Dict(Box::new(kind(&attr("item")?, false)?)),
        "typeddict" => Data::TypedDict(Box::new(TypedDict {
            fields: OnceLock::new(),
        })),
        "model" => Data::Model(Box::new(Nested {
            schema: OnceLock::new(),
        })),
        "union" => Data::Union(Box::new(union(converter)?)),
        _ => Data::Python,
    };
    Ok(Kind {
        data,
        converter: converter.clone().unbind(),
    })
}

fn union(converter: &Bound<'_, PyAny>) -> PyResult<Union> {
    let mut members = Vec::new();
    let json = converter.getattr("_json")?;
    let python = converter.getattr("_python")?;
    for (json, python) in json.try_iter()?.zip(python.try_iter()?) {
        let (member, json_types): (Bound<'_, PyAny>, Bound<'_, PyAny>) = json?.extract()?;
        let (_, python_types): (Bound<'_, PyAny>, Bound<'_, PyAny>) = python?.extract()?;
        members.push(Member {
            kind: kind(&member, false)?,
            json_types: json_types.unbind(),
            python_types: python_types.unbind(),
        });
    }
    let discriminator = converter.getattr("discriminator")?;
    Ok(Union {
        members,
        nullable: converter.getattr("nullable")?.extract()?,
        label: converter.getattr("label")?.extract()?,
        discriminator: if discriminator.is_none() {
            None
        } else {
            Some(Discriminator {
                field: discriminator.cast_into::<PyString>()?.unbind(),
                table: OnceLock::new(),
            })
        },
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
    let missing = errors::missing(py)?;
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
            kind: kind(&spec.getattr("converter")?, false)?,
            default: (!default.is(&missing)).then(|| default.unbind()),
            factory: (!factory.is_none()).then(|| factory.unbind()),
        });
    }
    Ok((fields, names))
}

/// The fields of a `_TypedDict` converter: its `(name, converter, required)` triples.
pub(crate) fn typeddict_fields(converter: &Bound<'_, PyAny>) -> PyResult<Vec<TypedDictField>> {
    let py = converter.py();
    let mut fields = Vec::new();
    for item in converter.getattr("fields")?.try_iter()? {
        let (key, field, required): (String, Bound<'_, PyAny>, bool) = item?.extract()?;
        fields.push(TypedDictField {
            name: PyString::intern(py, &key).unbind(),
            key,
            kind: kind(&field, false)?,
            required,
        });
    }
    Ok(fields)
}
