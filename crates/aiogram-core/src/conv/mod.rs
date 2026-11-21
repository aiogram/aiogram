//! Rust backend of the converter core (`aiogram/utils/_converters.py`, F-08, PD-35).
//!
//! A [`ModelSchema`] is compiled from a Python `ModelConverter` and replaces its `from_json`,
//! `load_json`, `from_flat` and `to_flat` on CPython. The walkers handle the common shapes
//! only; see [`fallback`] for how everything else gets the Python result.
//!
//! - [`fallback`]: the fast-path result type;
//! - [`kind`]: compiled field types;
//! - [`compile`]: Python converters -> kinds and fields;
//! - [`schema`]: the Python-facing class and instance building;
//! - [`dict`], [`json`], [`flat`]: the three walkers.
//!
//! This tree is independent of the generated Bot API code (08 §7 placement rules).

mod compile;
mod dict;
mod fallback;
mod flat;
mod json;
mod kind;
mod schema;

pub use schema::ModelSchema;
