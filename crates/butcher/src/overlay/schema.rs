//! The serde shape of every overlay file. Each struct denies unknown keys; rules that need more than serde (exactly
//! one of two keys, references into the IR) are in [`super::check`].

use std::collections::BTreeMap;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Deserializer};
use serde_json::Value;

use crate::ir::TypeRef;

pub type Map<T> = BTreeMap<String, T>;

/// Fill-DSL text, stored unparsed (C-07 parses it): `"self.chat.id"` or `{ expr = "...", when = "..." }`.
#[derive(Debug, Clone, PartialEq)]
pub struct Fill {
    pub expr: String,
    pub when: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FillTable {
    expr: String,
    #[serde(default)]
    when: Option<String>,
}

// ponytail: hand-written instead of `#[serde(untagged)]`, which drops the inner "unknown field" error
impl<'de> Deserialize<'de> for Fill {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Fill, D::Error> {
        struct FillVisitor;
        impl<'de> Visitor<'de> for FillVisitor {
            type Value = Fill;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("a fill expression string or a table `{ expr, when }`")
            }
            fn visit_str<E: de::Error>(self, v: &str) -> Result<Fill, E> {
                Ok(Fill {
                    expr: v.to_owned(),
                    when: None,
                })
            }
            fn visit_map<A: MapAccess<'de>>(self, map: A) -> Result<Fill, A::Error> {
                let t = FillTable::deserialize(de::value::MapAccessDeserializer::new(map))?;
                Ok(Fill {
                    expr: t.expr,
                    when: t.when,
                })
            }
        }
        deserializer.deserialize_any(FillVisitor)
    }
}

/// Kind 1, `names.toml`.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Names {
    /// type -> wire field -> Python name
    #[serde(default)]
    pub types: Map<Map<String>>,
    /// method -> wire param -> Python name
    #[serde(default)]
    pub methods: Map<Map<String>>,
    /// method -> param -> Python alias of its inline union (`sendMediaGroup.media` -> `MediaUnion`)
    #[serde(default)]
    pub union_aliases: Map<Map<String>>,
}

/// Kind 2, `enums/<Name>.toml`. At least one rule; several combine (`parse` + `static`).
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EnumDef {
    #[serde(default)]
    pub doc: Option<String>,
    #[serde(default)]
    pub parse: Option<Parse>,
    #[serde(default)]
    pub multi_parse: Option<MultiParse>,
    /// member name -> value
    #[serde(default, rename = "static")]
    pub static_members: Option<Map<Value>>,
    #[serde(default)]
    pub extract: Option<Extract>,
}

/// Values found by `regexp` in the description of one field or param: exactly one of `type` / `method`.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parse {
    #[serde(default, rename = "type")]
    pub ty: Option<String>,
    #[serde(default)]
    pub method: Option<String>,
    pub field: String,
    pub regexp: String,
}

/// One value per type, found by `regexp` in the description of `field` on each of `types`.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MultiParse {
    pub field: String,
    pub regexp: String,
    pub types: Vec<String>,
}

/// One member per field name of `type` (`UpdateType` from `Update`).
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Extract {
    #[serde(rename = "type")]
    pub ty: String,
    #[serde(default)]
    pub exclude: Vec<String>,
}

/// Kinds 3 and 12 (`datetime.toml`, `display.toml`): field lists per type, param lists per method.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Refs {
    #[serde(default)]
    pub types: Map<Vec<String>>,
    #[serde(default)]
    pub methods: Map<Vec<String>>,
}

/// Kind 4, `defaults.toml`: field / param -> bot-level `Default(...)` name.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Defaults {
    #[serde(default)]
    pub types: Map<Map<String>>,
    #[serde(default)]
    pub methods: Map<Map<String>>,
}

/// Kind 5, one entry of `shortcuts/<Type>.toml`.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Shortcut {
    #[serde(default)]
    pub method: Option<String>,
    /// `assert <path> is not None, "<message>"`
    #[serde(default)]
    pub require: Vec<Guard>,
    /// `assert <path> is None, "<message>"`
    #[serde(default)]
    pub forbid: Vec<Guard>,
    /// Params of `method` never forwarded.
    #[serde(default)]
    pub ignore: Vec<String>,
    /// Written by hand in `<type>_ext.rs` (D11): no `method`, no `fill`.
    #[serde(default)]
    pub handwritten: bool,
    #[serde(default)]
    pub fill: Map<Fill>,
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Guard {
    pub path: String,
    pub message: String,
}

/// Kind 6, `unions.toml`: exactly one of `tag` / `rules` (D85, D107).
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UnionRule {
    /// Field whose value picks the member.
    #[serde(default)]
    pub tag: Option<String>,
    /// First match wins; no match decodes as `Unknown`.
    #[serde(default)]
    pub rules: Vec<Rule>,
}

/// A predicate on one field: exactly one of `eq`, `ne`, `present = true`, `absent = true`.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Rule {
    pub member: String,
    pub field: String,
    #[serde(default)]
    pub eq: Option<Value>,
    #[serde(default)]
    pub ne: Option<Value>,
    #[serde(default)]
    pub present: bool,
    #[serde(default)]
    pub absent: bool,
}

/// Kind 7, `twins.toml`: overrides of the computed `Input*` twin merge (D18), keyed by the documented type.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Twin {
    #[serde(default = "yes")]
    pub merge: bool,
    #[serde(default)]
    pub required: Map<bool>,
}

fn yes() -> bool {
    true
}

/// Kind 8, `layout.toml` (01 §3.1).
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Layout {
    #[serde(default)]
    pub hot: Vec<String>,
    #[serde(default)]
    pub freelist: bool,
}

/// Kind 9, `heuristics.toml`: pins for facts the HTML heuristics infer.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Heuristics {
    /// method -> return type, in the IR `TypeRef` form (`{ array = { ref = "ChatMember" } }`)
    #[serde(default)]
    pub returns: Map<TypeRef>,
    /// type -> field -> constant
    #[serde(default)]
    pub consts: Map<Map<Value>>,
    /// union -> member types
    #[serde(default)]
    pub subtypes: Map<Vec<String>>,
    /// enum -> values
    #[serde(default)]
    pub enum_members: Map<Vec<Value>>,
}

/// Kind 10, `docs.toml`.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Docs {
    #[serde(default)]
    pub types: Map<Note>,
    #[serde(default)]
    pub methods: Map<Note>,
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Note {
    /// RST appended to the docstring.
    pub note: String,
}

/// Kind 11, `methods.toml` (R19, PD-25).
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Methods {
    #[serde(default)]
    pub idempotent: Map<bool>,
    /// Never retried by `RetryMiddleware` (`getUpdates`: the Poller owns it).
    #[serde(default)]
    pub excluded: Vec<String>,
}

/// Kinds 13 and 14, `content.toml`: content kinds in 3.x `content_type` match order.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Content {
    #[serde(default)]
    pub kind: Vec<ContentKind>,
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ContentKind {
    /// The 3.x `content_type` value, `"photo"`.
    pub name: String,
    /// The `Message` field that signals the kind.
    pub field: String,
    /// The `send_copy` mapping; absent fails `check` (C-23).
    #[serde(default)]
    pub copy: Option<SendCopy>,
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SendCopy {
    pub method: String,
    #[serde(default)]
    pub fill: Map<Fill>,
}

/// Kind 15, one entry of `events.toml`, keyed by update type; an empty table is valid.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Event {
    #[serde(default)]
    pub user: Option<Fill>,
    #[serde(default)]
    pub chat: Option<Fill>,
    #[serde(default)]
    pub thread_id: Option<Fill>,
    #[serde(default)]
    pub business_connection_id: Option<Fill>,
}

/// Kind 17, `errors.toml` (PD-24): `errors.json` message -> `ErrorReason` member name.
#[derive(Debug, Clone, Default, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Errors {
    #[serde(default)]
    pub names: Map<String>,
}
