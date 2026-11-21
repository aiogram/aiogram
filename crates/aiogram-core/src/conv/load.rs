//! `from_json`: JSON-shaped Python values -> converted values.

use pyo3::exceptions::{PyArithmeticError, PyOverflowError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple, PyType};

use super::errors::{self, at, expected};
use super::kind::{Data, Discriminator, Enumeration, Kind, Literal, Text, TypedDict, Union};

/// A walker over one kind: [`load`] (`from_json`) or [`super::dump::dump`] (`to_json`).
pub(crate) type Walk =
    for<'py> fn(Python<'py>, &Bound<'py, PyAny>, &Kind, u32) -> PyResult<Bound<'py, PyAny>>;

pub(crate) fn load<'py>(
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
        Data::Text(text) => {
            if !value.is_instance_of::<PyString>() {
                return Err(expected(py, &format!("a {} string", text.name), value));
            }
            parse_text(py, text, value)
        }
        Data::Enum(enumeration) => enum_member(py, enumeration, value),
        Data::Literal(literal) => literal_value(py, literal, value),
        Data::Optional { inner, .. } => {
            if value.is_none() {
                Ok(value.clone())
            } else {
                load(py, value, inner, depth)
            }
        }
        Data::Sequence { item, collect, .. } => {
            errors::check_depth(depth)?;
            let out = PyList::empty(py);
            let push = |index: usize, element: Bound<'py, PyAny>| -> PyResult<()> {
                let converted = load(py, &element, item, depth + 1)
                    .map_err(|e| at(py, e, || Ok(format!("[{index}]"))))?;
                out.append(converted)
            };
            if let Ok(list) = value.cast::<PyList>() {
                for (index, element) in list.iter().enumerate() {
                    push(index, element)?;
                }
            } else if let Ok(tuple) = value.cast::<PyTuple>() {
                for (index, element) in tuple.iter().enumerate() {
                    push(index, element)?;
                }
            } else {
                return Err(expected(py, "an array", value));
            }
            collect.finish(out)
        }
        Data::Dict(item) => dict(py, value, item, depth, load),
        Data::TypedDict(typed) => typed_dict(py, typed, &kind.converter, value, depth, load),
        Data::Model(nested) => nested
            .schema(py, &kind.converter)?
            .get()
            .load(py, value, depth + 1),
        Data::Union(union) => union_load(py, union, &kind.converter, value, depth),
        Data::Python => kind
            .converter
            .bind(py)
            .call_method1(pyo3::intern!(py, "from_json"), (value,)),
    }
}

pub(crate) fn string<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    if value.is_instance_of::<PyString>() {
        Ok(value.clone())
    } else {
        Err(expected(py, "a string", value))
    }
}

pub(crate) fn boolean<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    if value.is_instance_of::<PyBool>() {
        Ok(value.clone())
    } else {
        Err(expected(py, "a boolean", value))
    }
}

/// `_Int`: exact `int` as is, an `int` subclass (not `bool`) through `int()`.
pub(crate) fn int<'py>(py: Python<'py>, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    if value.is_exact_instance_of::<PyInt>() {
        return Ok(value.clone());
    }
    if value.is_instance_of::<PyInt>() && !value.is_instance_of::<PyBool>() {
        return py.get_type::<PyInt>().call1((value,));
    }
    Err(expected(py, "an integer", value))
}

/// `_Float`: exact `float` as is, any other `int` / `float` (not `bool`) through `float()`.
pub(crate) fn float<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    if value.is_exact_instance_of::<PyFloat>() {
        return Ok(value.clone());
    }
    if (value.is_instance_of::<PyInt>() || value.is_instance_of::<PyFloat>())
        && !value.is_instance_of::<PyBool>()
    {
        // an int too large for a float (10 ** 1000) is a conversion error, not OverflowError
        return py.get_type::<PyFloat>().call1((value,)).map_err(|error| {
            if error.is_instance_of::<PyOverflowError>(py) {
                expected(py, "a number", value)
            } else {
                error
            }
        });
    }
    Err(expected(py, "a number", value))
}

/// `_Text._parse`: a `ValueError` / `ArithmeticError` from the parser is a conversion error.
pub(crate) fn parse_text<'py>(
    py: Python<'py>,
    text: &Text,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    text.parse.bind(py).call1((value,)).map_err(|error| {
        if error.is_instance_of::<PyValueError>(py) || error.is_instance_of::<PyArithmeticError>(py)
        {
            expected(py, &format!("a {} string", text.name), value)
        } else {
            error
        }
    })
}

fn type_and_value<'py>(value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyTuple>> {
    PyTuple::new(value.py(), [value.get_type().into_any(), value.clone()])
}

/// `_Enum`: matched by `(type(value), value)`, so `true` or `1.0` never load an `IntEnum`.
fn enum_member<'py>(
    py: Python<'py>,
    enumeration: &Enumeration,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let miss = || expected(py, &format!("a {} value", enumeration.name), value);
    if let Ok(Some(member)) = enumeration
        .by_json
        .bind(py)
        .get_item(type_and_value(value)?)
    {
        return Ok(member);
    }
    if !enumeration.has_missing {
        return Err(miss()); // a miss, or an unhashable value
    }
    // a tolerant enum: `tp(value)` runs its _missing_ hook; a ValueError is still a miss
    enumeration.tp.bind(py).call1((value,)).map_err(|error| {
        if error.is_instance_of::<PyValueError>(py) {
            miss()
        } else {
            error
        }
    })
}

/// `_Literal`: `(type(value), value) in _json`; an unhashable value is a miss.
pub(crate) fn literal_value<'py>(
    py: Python<'py>,
    literal: &Literal,
    value: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    match literal.json.bind(py).contains(type_and_value(value)?) {
        Ok(true) => Ok(value.clone()),
        _ => Err(expected(py, &literal.label, value)),
    }
}

/// `_Dict`: a `dict` with `str` keys, each value walked.
pub(crate) fn dict<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    item: &Kind,
    depth: u32,
    walk: Walk,
) -> PyResult<Bound<'py, PyAny>> {
    errors::check_depth(depth)?;
    let source = value
        .cast::<PyDict>()
        .map_err(|_| expected(py, "an object", value))?;
    let out = PyDict::new(py);
    // a critical section on free-threaded builds
    source.locked_for_each(|key, element| {
        if !key.is_instance_of::<PyString>() {
            return Err(expected(py, "a string key", &key));
        }
        let converted = walk(py, &element, item, depth + 1)
            .map_err(|e| at(py, e, || Ok(format!("[{}]", key.repr()?))))?;
        out.set_item(key, converted)
    })?;
    Ok(out.into_any())
}

static MAPPING: PyOnceLock<Py<PyType>> = PyOnceLock::new();

/// Field access on a model / TypedDict input: an exact `dict` directly, any other `Mapping`
/// through its `get` and `in`, as the Python code does.
pub(crate) enum Getter<'py> {
    Dict(Bound<'py, PyDict>),
    Mapping(Bound<'py, PyAny>, Bound<'py, PyAny>),
}

impl<'py> Getter<'py> {
    pub(crate) fn new(py: Python<'py>, value: &Bound<'py, PyAny>) -> PyResult<Self> {
        if let Ok(dict) = value.cast_exact::<PyDict>() {
            return Ok(Self::Dict(dict.clone()));
        }
        let mapping = MAPPING.get_or_try_init(py, || {
            py.import("collections.abc")?
                .getattr("Mapping")?
                .cast_into::<PyType>()
                .map(Bound::unbind)
                .map_err(PyErr::from)
        })?;
        if value.is_instance(mapping.bind(py))? {
            Ok(Self::Mapping(value.clone(), errors::missing(py)?))
        } else {
            Err(expected(py, "an object", value))
        }
    }

    pub(crate) fn get(&self, name: &Bound<'py, PyString>) -> PyResult<Option<Bound<'py, PyAny>>> {
        match self {
            Self::Dict(dict) => dict.get_item(name),
            Self::Mapping(mapping, missing) => {
                let item =
                    mapping.call_method1(pyo3::intern!(mapping.py(), "get"), (name, missing))?;
                Ok(if item.is(missing) { None } else { Some(item) })
            }
        }
    }

    /// `name in value`, for the "set fields" record.
    pub(crate) fn contains(&self, name: &Bound<'py, PyString>, got: bool) -> PyResult<bool> {
        match self {
            Self::Dict(_) => Ok(got),
            Self::Mapping(mapping, _) => mapping.contains(name),
        }
    }
}

/// `_TypedDict._convert`: a plain dict of the declared keys present, in declaration order.
pub(crate) fn typed_dict<'py>(
    py: Python<'py>,
    typed: &TypedDict,
    converter: &Py<PyAny>,
    value: &Bound<'py, PyAny>,
    depth: u32,
    walk: Walk,
) -> PyResult<Bound<'py, PyAny>> {
    errors::check_depth(depth)?;
    let fields = typed.fields(py, converter)?;
    let getter = Getter::new(py, value)?;
    let out = PyDict::new(py);
    for field in fields {
        let name = field.name.bind(py);
        match getter.get(name)? {
            Some(raw) => {
                let converted = walk(py, &raw, &field.kind, depth + 1)
                    .map_err(|e| at(py, e, || Ok(format!(".{}", field.key))))?;
                out.set_item(name, converted)?;
            }
            None if field.required => return Err(errors::field_required(py, &field.key)),
            None => {}
        }
    }
    Ok(out.into_any())
}

/// The members to try for a value of `tp`: those whose types match it exactly first, then the
/// rest, each in declaration order (`_Union._order`).
pub(crate) fn ordered<'a>(
    py: Python<'_>,
    union: &'a Union,
    tp: &Bound<'_, PyType>,
    json: bool,
) -> PyResult<Vec<&'a Kind>> {
    let mut order = Vec::with_capacity(union.members.len());
    let mut exact = 0;
    for member in &union.members {
        let types = if json {
            &member.json_types
        } else {
            &member.python_types
        };
        if types.bind(py).contains(tp)? {
            order.insert(exact, &member.kind);
            exact += 1;
        } else {
            order.push(&member.kind);
        }
    }
    Ok(order)
}

/// The first member that accepts `value`; only a `ConversionError` moves to the next one.
pub(crate) fn first<'py>(
    py: Python<'py>,
    union: &Union,
    members: Vec<&Kind>,
    value: &Bound<'py, PyAny>,
    depth: u32,
    walk: Walk,
) -> PyResult<Bound<'py, PyAny>> {
    for member in members {
        match walk(py, value, member, depth) {
            Ok(result) => return Ok(result),
            Err(error) if errors::is_conversion(py, &error) => {}
            Err(error) => return Err(error),
        }
    }
    Err(expected(py, &union.label, value))
}

fn union_load<'py>(
    py: Python<'py>,
    union: &Union,
    converter: &Py<PyAny>,
    value: &Bound<'py, PyAny>,
    depth: u32,
) -> PyResult<Bound<'py, PyAny>> {
    if union.nullable && value.is_none() {
        return Ok(value.clone());
    }
    if let Some(discriminator) = &union.discriminator {
        return discriminated(py, union, discriminator, converter, value, depth);
    }
    let members = ordered(py, union, &value.get_type(), true)?;
    first(py, union, members, value, depth, load)
}

fn discriminated<'py>(
    py: Python<'py>,
    union: &Union,
    discriminator: &Discriminator,
    converter: &Py<PyAny>,
    value: &Bound<'py, PyAny>,
    depth: u32,
) -> PyResult<Bound<'py, PyAny>> {
    let field = discriminator.field.bind(py);
    let Some(tag) = Getter::new(py, value)?.get(field)? else {
        return Err(errors::field_required(py, &field.extract::<String>()?));
    };
    let (table, label) = crate::conv::kind::once(&discriminator.table, || -> PyResult<_> {
        let table = converter
            .bind(py)
            .call_method0(pyo3::intern!(py, "_tag_table"))?
            .cast_into::<PyDict>()?;
        let label = converter
            .bind(py)
            .getattr(pyo3::intern!(py, "tag_label"))?
            .extract()?;
        Ok((table.unbind(), label))
    })?;
    let member = match table.bind(py).get_item(type_and_value(&tag)?) {
        Ok(Some(member)) => member,
        _ => {
            let error = expected(py, label, &tag);
            return Err(at(py, error, || {
                Ok(format!(".{}", field.extract::<String>()?))
            }));
        }
    };
    // the tag table maps to the union's own member converters
    let kind = union
        .members
        .iter()
        .map(|member| &member.kind)
        .find(|kind| kind.converter.bind(py).is(&member))
        .ok_or_else(|| PyRuntimeError::new_err("discriminator tag maps to a foreign converter"))?;
    load(py, value, kind, depth)
}

#[cfg(test)]
mod tests {
    use pyo3::exceptions::PyRecursionError;
    use pyo3::prelude::*;
    use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyType};

    use super::load;
    use crate::conv::errors::MAX_DEPTH;
    use crate::conv::kind::{Collect, Data, Kind};

    fn with_python(test: impl for<'py> FnOnce(Python<'py>)) {
        Python::initialize();
        Python::attach(test);
    }

    fn kind(py: Python<'_>, data: Data) -> Kind {
        Kind {
            data,
            converter: py.None(),
        }
    }

    fn sequence(py: Python<'_>, item: Data, collect: Collect, tp: Bound<'_, PyType>) -> Kind {
        kind(
            py,
            Data::Sequence {
                item: Box::new(kind(py, item)),
                collect,
                tp: tp.unbind(),
            },
        )
    }

    #[test]
    fn exact_scalars_pass_through() {
        with_python(|py| {
            let one = 1i64.into_pyobject(py).unwrap().into_any();
            assert!(load(py, &one, &kind(py, Data::Int), 0).unwrap().is(&one));
            let float = load(py, &one, &kind(py, Data::Float), 0).unwrap();
            assert_eq!(float.extract::<f64>().unwrap(), 1.0);
        });
    }

    #[test]
    fn sequences_build_their_container() {
        with_python(|py| {
            let items = PyList::new(py, [1i64, 2, 2]).unwrap().into_any();
            let set = load(
                py,
                &items,
                &sequence(py, Data::Int, Collect::Set, py.get_type::<PySet>()),
                0,
            )
            .unwrap();
            assert!(set.is_instance_of::<PySet>());
            assert_eq!(set.len().unwrap(), 2);
            let frozen_kind = sequence(
                py,
                Data::Int,
                Collect::FrozenSet,
                py.get_type::<PyFrozenSet>(),
            );
            assert!(
                load(py, &items, &frozen_kind, 0)
                    .unwrap()
                    .is_instance_of::<PyFrozenSet>()
            );
        });
    }

    #[test]
    fn dict_values_are_converted() {
        with_python(|py| {
            let source = PyDict::new(py);
            source.set_item("a", 1i64).unwrap();
            let loaded = load(
                py,
                source.as_any(),
                &kind(py, Data::Dict(Box::new(kind(py, Data::Float)))),
                0,
            )
            .unwrap();
            assert_eq!(loaded.get_item("a").unwrap().extract::<f64>().unwrap(), 1.0);
        });
    }

    #[test]
    fn nesting_beyond_the_limit_is_a_recursion_error() {
        with_python(|py| {
            let items = PyList::new(py, [1i64]).unwrap().into_any();
            let list = sequence(py, Data::Int, Collect::List, py.get_type::<PyList>());
            let error = load(py, &items, &list, MAX_DEPTH + 1).unwrap_err();
            assert!(error.is_instance_of::<PyRecursionError>(py));
        });
    }
}
