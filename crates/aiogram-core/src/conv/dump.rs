//! `to_json`: converted values -> JSON-shaped Python values (validates Python values).

use pyo3::prelude::*;
use pyo3::types::{PyList, PyType};

use super::errors::{self, at, expected};
use super::kind::{Data, Kind, Text};
use super::load::{self, boolean, first, float, int, literal_value, ordered, string, typed_dict};

pub(crate) fn dump<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    kind: &Kind,
    depth: u32,
) -> PyResult<Bound<'py, PyAny>> {
    match &kind.data {
        Data::Str => string(py, value),
        Data::Int => int(py, value),
        Data::Float => float(py, value),
        Data::Bool => boolean(py, value),
        Data::Text(text) => text.to_text.bind(py).call1((check_text(py, text, value)?,)),
        Data::Enum(enumeration) => {
            if !value.is_instance(enumeration.tp.bind(py))? {
                return Err(expected(
                    py,
                    &format!("a {} member", enumeration.name),
                    value,
                ));
            }
            value.getattr(pyo3::intern!(py, "value"))
        }
        Data::Literal(literal) => literal_value(py, literal, value),
        Data::Optional { inner, .. } => {
            if value.is_none() {
                Ok(value.clone())
            } else {
                dump(py, value, inner, depth)
            }
        }
        Data::Sequence { item, tp, .. } => {
            errors::check_depth(depth)?;
            let tp = tp.bind(py);
            if !value.is_instance(tp)? {
                return Err(expected(py, &format!("a {}", type_name(tp)?), value));
            }
            let out = PyList::empty(py);
            for (index, element) in value.try_iter()?.enumerate() {
                let converted = dump(py, &element?, item, depth + 1)
                    .map_err(|e| at(py, e, || Ok(format!("[{index}]"))))?;
                out.append(converted)?;
            }
            Ok(out.into_any())
        }
        Data::Dict(item) => load::dict(py, value, item, depth, dump),
        Data::TypedDict(typed) => typed_dict(py, typed, &kind.converter, value, depth, dump),
        Data::Model(nested) => {
            nested
                .schema(py, &kind.converter)?
                .get()
                .to_json(py, value, depth + 1)
        }
        Data::Union(union) => {
            if union.nullable && value.is_none() {
                return Ok(value.clone());
            }
            let members = ordered(py, union, &value.get_type(), false)?;
            first(py, union, members, value, depth, dump)
        }
        Data::Python => kind
            .converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "to_json"), (value,)),
    }
}

/// `_Text._check`: an instance of the type, and not of `reject` (a `datetime` for `date`).
pub(crate) fn check_text<'py, 'a>(
    py: Python<'py>,
    text: &Text,
    value: &'a Bound<'py, PyAny>,
) -> PyResult<&'a Bound<'py, PyAny>> {
    let rejected = match &text.reject {
        Some(reject) => value.is_instance(reject.bind(py))?,
        None => false,
    };
    if value.is_instance(text.tp.bind(py))? && !rejected {
        Ok(value)
    } else {
        Err(expected(py, &format!("a {}", text.name), value))
    }
}

pub(crate) fn type_name(tp: &Bound<'_, PyType>) -> PyResult<String> {
    tp.getattr("__name__")?.extract()
}
