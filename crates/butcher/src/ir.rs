//! The IR: what every source adapter produces and every emitter reads (plan C-01).
//!
//! `ir.html.json`, `ir.openapi.json`, `ir.errors.json` and the merged `ir.json` are all an [`Ir`]; a list a source
//! does not produce is empty and omitted. Format rules:
//! - every struct denies unknown keys; struct keys are written in declaration order, maps sorted (`BTreeMap`);
//! - entity lists keep the source document order (the merged IR keeps HTML order);
//! - 2-space indented JSON, trailing newline, LF; no timestamps or paths;
//! - the format only grows by optional fields (`Option` / empty `Vec`, omitted when empty), so older snapshots
//!   still load; a rename or removal rewrites the committed snapshots in the same PR.

use std::collections::BTreeMap;
use std::path::Path;

use serde::{Deserialize, Serialize};
use serde_json::{Number, Value};

use crate::Error;

/// Docs are the HTML fragment of the source; plain text and RST are derived at emit time.
pub type Doc = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Ir {
    pub header: Header,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub types: Vec<Type>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub methods: Vec<Method>,
    /// Enums the source itself names; inline value sets live on fields and params (`values`).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub enums: Vec<Enum>,
    /// Abstract types (`ChatMember`, `MaybeInaccessibleMessage`, ...).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub unions: Vec<Union>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub errors: Vec<ErrorEntry>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Header {
    /// `"10.4"`
    pub api_version: String,
    /// ISO date, `"2026-11-09"`; the OpenAPI schema has none.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub api_date: Option<String>,
    /// In `html`, `openapi`, `errors` order.
    pub sources: Vec<Source>,
    pub html_only: bool,
}

/// Declaration order is the order `Header.sources` must follow.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Source {
    Html,
    Openapi,
    Errors,
}

/// An inferred fact and where it came from.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Fact<T> {
    pub value: T,
    #[serde(default, skip_serializing_if = "Provenance::is_explicit")]
    pub by: Provenance,
}

impl<T> Fact<T> {
    pub fn explicit(value: T) -> Self {
        Fact {
            value,
            by: Provenance::Explicit,
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
pub enum Provenance {
    /// Read straight from the source (a table cell, a schema keyword). Omitted in JSON.
    #[default]
    Explicit,
    /// Inferred by a named rule, e.g. `"returns.r07"`, `"merge.previous_snapshot"`.
    Heuristic(String),
    Overlay {
        file: String,
        key: String,
    },
}

impl Provenance {
    pub fn is_explicit(&self) -> bool {
        matches!(self, Provenance::Explicit)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Direction {
    Request,
    Response,
    Both,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Type {
    /// Wire name, `"Message"`.
    pub name: String,
    /// Docs section title, `"Available types"`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub section: Option<String>,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub doc: Doc,
    /// Which sides of the wire use the type at all.
    pub direction: Fact<Direction>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub fields: Vec<Field>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Field {
    /// Wire name, `"from"`.
    pub name: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub doc: Doc,
    #[serde(rename = "type")]
    pub ty: Fact<TypeRef>,
    /// Absent: not accepted in requests (read-only).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub request: Option<Usage>,
    /// Absent: never returned (write-only).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub response: Option<Usage>,
    /// Inline enum value set (string or integer members).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub values: Option<Fact<Vec<Value>>>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub constraints: Vec<Fact<Constraint>>,
}

/// Direction-specific facts of a field (D118), kept through the D18 twin merge.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Usage {
    pub required: Fact<bool>,
    /// A non-`True` constant (`"type": "photo"`); `True` itself is [`Prim::True`].
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub constant: Option<Fact<Value>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default: Option<Fact<Value>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Method {
    /// Wire name, `"sendMessage"`.
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub section: Option<String>,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub doc: Doc,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub params: Vec<Param>,
    pub returns: Fact<TypeRef>,
}

/// A method parameter: request-only by definition.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Param {
    pub name: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub doc: Doc,
    #[serde(rename = "type")]
    pub ty: Fact<TypeRef>,
    pub required: Fact<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub constant: Option<Fact<Value>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default: Option<Fact<Value>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub values: Option<Fact<Vec<Value>>>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub constraints: Vec<Fact<Constraint>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
pub enum TypeRef {
    Prim(Prim),
    /// A type, union or enum name; `InputFile` is a `Ref`.
    Ref(String),
    Array(Box<TypeRef>),
    /// Inline `Integer or String`; member order is kept.
    Union(Vec<TypeRef>),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Prim {
    /// Width unknown (HTML).
    Int,
    Int32,
    Int64,
    Float,
    String,
    Bool,
    /// The Bot API's `True`: a boolean that is always `true`.
    True,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", deny_unknown_fields)]
pub enum Constraint {
    MinLength(u64),
    MaxLength(u64),
    MinItems(u64),
    MaxItems(u64),
    /// `Number` keeps the integer / float form of the source.
    Minimum(Number),
    Maximum(Number),
    Pattern(String),
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Union {
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub section: Option<String>,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub doc: Doc,
    /// Member type names; the order is semantic.
    pub members: Fact<Vec<String>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub discriminator: Option<Fact<Discriminator>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Discriminator {
    /// Wire name of the tag field.
    pub field: String,
    /// Tag value -> member type name.
    pub mapping: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Enum {
    pub name: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub doc: Doc,
    pub values: Fact<Vec<Value>>,
}

/// One `errors.json` entry (C-05).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ErrorEntry {
    /// HTTP / Bot API error code; MTProto-derived codes can be negative (`-503`).
    pub code: i32,
    pub message: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mtproto: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub template: Option<Template>,
    /// Methods the entry applies to, when the source lists them.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub methods: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Template {
    /// `%s` / `%d` in message order.
    pub placeholders: Vec<Placeholder>,
    /// Anchored regex matching the rendered message.
    pub regex: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Placeholder {
    S,
    D,
}

impl Ir {
    pub fn load(path: &Path) -> Result<Ir, Error> {
        let text = crate::read(path)?;
        let mut de = serde_json::Deserializer::from_str(&text);
        let ir: Ir =
            serde_path_to_error::deserialize(&mut de).map_err(|e| crate::parse_error(path, e))?;
        de.end()
            .map_err(|e| crate::invalid(path, (".".to_owned(), e.to_string())))?;
        ir.check().map_err(|e| crate::invalid(path, e))?;
        Ok(ir)
    }

    /// Invariants serde cannot express, as `(key path, message)`.
    fn check(&self) -> Result<(), (String, String)> {
        if !self.header.sources.is_sorted_by(|a, b| a < b) {
            let message = "must be unique, in html, openapi, errors order";
            return Err(("header.sources".to_owned(), message.to_owned()));
        }
        Ok(())
    }

    pub fn write(&self, path: &Path) -> Result<(), Error> {
        crate::write(path, &self.to_json()?)
    }

    /// The exact bytes [`Ir::write`] writes.
    pub fn to_json(&self) -> Result<String, Error> {
        self.check().map_err(crate::invalid_output)?;
        let mut text =
            serde_json::to_string_pretty(self).map_err(|e| Error::Encode(e.to_string()))?;
        text.push('\n');
        Ok(text)
    }
}
