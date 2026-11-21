//! The converter core (`aiogram/utils/_converters.py`, F-08, PD-35): the Python module compiles
//! annotations into converters, and this tree does all per-value conversion.
//!
//! - [`errors`]: `ConversionError` with field paths, the depth guard;
//! - [`kind`]: compiled field types;
//! - [`compile`]: Python converters -> kinds and fields;
//! - [`load`] (`from_json`), [`dump`] (`to_json`), [`json`] (one-pass `load_json`),
//!   [`flat`] (callback-data `from_str` / `to_str`): the walkers;
//! - [`schema`]: the Python-facing `ModelSchema` and `KindCore`, model building.
//!
//! This tree is independent of the generated Bot API code (08 §7 placement rules).

mod compile;
mod dump;
mod errors;
mod flat;
mod json;
mod kind;
mod load;
mod schema;

pub use schema::{KindCore, ModelSchema};
