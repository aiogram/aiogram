//! The converter core (F-08, PD-36, plan-10). `aiogram/utils/_converters.py` resolves
//! annotations and builds [`ir`] objects through typed constructors; this tree does every
//! conversion.
//!
//! - [`ir`]: the Python -> Rust interface: `Kind`, `KindCell`, `Field`;
//! - [`model`]: `ModelCore`, the field table of a class, and discriminator tags;
//! - [`construct`]: building instances (generic setattr, `__fields_set__`, `__post_init__`) and
//!   the validating `__init__`;
//! - [`check`]: strict checks of Python values;
//! - [`scalars`]: Python glue of the scalar kinds, shared by every codec;
//! - [`walk`]: error collection, mapping access, dict iteration and smart-union trials;
//! - [`errors`]: error lines kept in Rust, one `ConversionError` at the boundary;
//! - [`native`]: pure-Rust text formats (UUID, ISO 8601, base64, JSON numbers and strings);
//! - [`json`]: dict load, one-pass bytes load, dict dump, bytes dump;
//! - [`flat`]: the positional flat-string codec (callback data);
//! - [`schema`]: the Python-facing `JsonSchema`, `FlatSchema`, `JsonCodec`.
//!
//! This tree is independent of the generated Bot API code (08 §7 placement rules).

mod check;
mod construct;
pub(crate) mod errors;
mod flat;
pub(crate) mod ir;
mod json;
pub(crate) mod model;
mod native;
mod scalars;
mod schema;
mod walk;

use pyo3::prelude::*;

use errors::converters_init;
use ir::{Field, Kind, KindCell};
use model::ModelCore;
use schema::{FlatSchema, JsonCodec, JsonSchema};

/// Fills `aiogram._core.conv` (stub: `aiogram/_core/conv.pyi`).
pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Kind>()?;
    m.add_class::<KindCell>()?;
    m.add_class::<Field>()?;
    m.add_class::<ModelCore>()?;
    m.add_class::<JsonSchema>()?;
    m.add_class::<FlatSchema>()?;
    m.add_class::<JsonCodec>()?;
    m.add_function(wrap_pyfunction!(converters_init, m)?)
}
