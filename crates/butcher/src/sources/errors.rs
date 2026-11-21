//! `errors.json` adapter (plan C-05): the Bot API error catalogue as `ir.errors.json`.
//!
//! Input shape (undocumented, probed on `corefork.telegram.org/bots/errors.json`):
//! `errors: {"<http code>": {"<message>": ["method", ...]}}`, `mtproto_errors: {"<message>": ["CODE", ...]}`,
//! plus `version`, `mtproto_layer`, `parameters` and `mtproto_descriptions`, which the IR does not carry.
//!
//! A message with `%s` / `%d` is a template. Its regex is anchored, has one capture group per placeholder, and
//! stays in the subset Python `re` and Rust `regex` share: `%s` is `([\s\S]*?)` (it can render empty or span lines), `%d` is `(-?\d+)`.
//! Templates overlap (`entity %s` also matches `entity begins after ... %d`), so the regexes alone are ambiguous.
//! Lookup rule for consumers: the exact message first, then the matching template with the longest
//! [`literal_len`]; the catalogue guarantees that template is unique.

use std::collections::BTreeMap;
use std::path::Path;

use serde::Deserialize;
use serde_json::Value;

use crate::Error;
use crate::ir::{ErrorEntry, Header, Ir, Placeholder, Source, Template};

const KNOWN_KEYS: [&str; 6] = [
    "version",
    "mtproto_layer",
    "errors",
    "parameters",
    "mtproto_errors",
    "mtproto_descriptions",
];

#[derive(Deserialize)]
struct Raw {
    version: String,
    /// code -> message -> methods
    errors: BTreeMap<i32, BTreeMap<String, Vec<String>>>,
    #[serde(default)]
    mtproto_errors: BTreeMap<String, Vec<String>>,
}

/// Parsed catalogue plus the warnings (new top-level keys, unused `mtproto_errors` keys).
pub struct Parsed {
    pub ir: Ir,
    pub warnings: Vec<String>,
}

pub fn parse(path: &Path) -> Result<Parsed, Error> {
    from_str(&crate::read(path)?, path)
}

/// `path` is only used in error messages.
pub fn from_str(text: &str, path: &Path) -> Result<Parsed, Error> {
    let value: Value = serde_json::from_str(text)
        .map_err(|e| crate::invalid(path, (".".to_owned(), e.to_string())))?;
    let Value::Object(mut map) = value else {
        return Err(crate::invalid(
            path,
            (".".to_owned(), "expected an object".to_owned()),
        ));
    };
    let mut warnings = Vec::new();
    for key in map.keys().filter(|k| !KNOWN_KEYS.contains(&k.as_str())) {
        warnings.push(format!("unknown top-level key `{key}` ignored"));
    }
    map.retain(|k, _| KNOWN_KEYS.contains(&k.as_str()));
    let raw: Raw = serde_path_to_error::deserialize(Value::Object(map))
        .map_err(|e| crate::parse_error(path, e))?;

    let mut errors = Vec::new();
    for (code, messages) in &raw.errors {
        for (message, methods) in messages {
            let template = compile(message)
                .map_err(|m| crate::invalid(path, (format!("errors.{code}[\"{message}\"]"), m)))?;
            let mtproto = match raw.mtproto_errors.get(message).map(Vec::as_slice) {
                // several codes share the message: the IR holds one, so none is picked
                Some([one]) => Some(one.clone()),
                _ => None,
            };
            errors.push(ErrorEntry {
                code: *code,
                message: message.clone(),
                mtproto,
                template,
                methods: methods.clone(),
            });
        }
    }
    for message in raw.mtproto_errors.keys() {
        if !raw.errors.values().any(|m| m.contains_key(message)) {
            warnings.push(format!(
                "mtproto_errors key `{message}` has no entry in errors"
            ));
        }
    }
    let header = Header {
        api_version: raw.version,
        api_date: None,
        sources: vec![Source::Errors],
        html_only: false,
    };
    let ir = Ir {
        header,
        types: vec![],
        methods: vec![],
        enums: vec![],
        unions: vec![],
        errors,
    };
    Ok(Parsed { ir, warnings })
}

/// The message without its placeholders: how specific a template is.
pub fn literal_len(message: &str) -> usize {
    message.len() - 2 * message.matches("%s").count() - 2 * message.matches("%d").count()
}

/// `None` for a plain message, an error text for a `%` that is not `%s` / `%d`.
fn compile(message: &str) -> Result<Option<Template>, String> {
    let mut placeholders = Vec::new();
    let mut regex = String::from("^");
    let mut rest = message;
    while let Some(at) = rest.find('%') {
        escape(&rest[..at], &mut regex);
        match rest.as_bytes().get(at + 1) {
            Some(b's') => {
                placeholders.push(Placeholder::S);
                regex.push_str(r"([\s\S]*?)");
            }
            Some(b'd') => {
                placeholders.push(Placeholder::D);
                regex.push_str(r"(-?\d+)");
            }
            _ => return Err("`%` is not followed by `s` or `d`".to_owned()),
        }
        rest = &rest[at + 2..];
    }
    if placeholders.is_empty() {
        return Ok(None);
    }
    escape(rest, &mut regex);
    regex.push('$');
    Ok(Some(Template {
        placeholders,
        regex,
    }))
}

/// Backslash-escapes the characters both Python `re` and Rust `regex` treat as syntax.
fn escape(literal: &str, out: &mut String) {
    for c in literal.chars() {
        if "\\.+*?()|[]{}^$#&-~".contains(c) {
            out.push('\\');
        }
        out.push(c);
    }
}
