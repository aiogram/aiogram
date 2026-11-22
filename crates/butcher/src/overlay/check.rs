//! References from the overlay into the IR, and the rules serde cannot express. Every error names the file, the
//! key path, and the closest IR name when one is near.

use std::collections::BTreeSet;
use std::path::PathBuf;

use super::Overlay;
use super::schema::{Fill, Map, Refs};
use crate::Error;
use crate::ir::{Field, Ir, Method, Param, Prim, Source, Type, TypeRef};

const KEYWORDS: [&str; 35] = [
    "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import",
    "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while",
    "with", "yield",
];

pub(super) fn check(overlay: &Overlay, ir: &Ir) -> Vec<Error> {
    let mut c = Checker {
        overlay,
        ir,
        file: PathBuf::new(),
        errors: Vec::new(),
    };
    c.names();
    c.enums();
    c.refs(
        "datetime.toml",
        &overlay.datetime,
        ("an integer", holds_integer),
    );
    c.defaults();
    c.shortcuts();
    c.unions();
    c.twins();
    c.layout();
    c.heuristics();
    c.docs();
    c.methods();
    c.refs("display.toml", &overlay.display, ("a string", holds_string));
    c.content();
    c.events();
    c.bases();
    c.errors();
    let mut errors = c.errors;
    // stable: within a file, errors keep the order of its keys (`kind[2]` before `kind[10]`)
    errors.sort_by(|a, b| a.0.cmp(&b.0));
    errors
        .into_iter()
        .map(|(path, at, message)| crate::invalid(&path, (at, message)))
        .collect()
}

struct Checker<'a> {
    overlay: &'a Overlay,
    ir: &'a Ir,
    /// The file being checked.
    file: PathBuf,
    /// `(file, key path, message)`
    errors: Vec<(PathBuf, String, String)>,
}

// ponytail: lookups are linear scans over the IR lists; a few thousand refs against ~300 entities is instant.
impl<'a> Checker<'a> {
    fn at(&mut self, file: &str) {
        self.file = self.overlay.root.join(file);
    }

    fn fail(&mut self, at: impl Into<String>, message: impl Into<String>) {
        let error = (self.file.clone(), at.into(), message.into());
        self.errors.push(error);
    }

    fn missing<'n>(
        &mut self,
        at: impl Into<String>,
        what: &str,
        name: &str,
        candidates: impl Iterator<Item = &'n str>,
    ) {
        let hint = closest(name, candidates)
            .map(|c| format!(" (closest: `{c}`)"))
            .unwrap_or_default();
        self.fail(at, format!("no {what} `{name}`{hint}"));
    }

    fn ty(&mut self, at: &str, name: &str) -> Option<&'a Type> {
        let ir = self.ir;
        let found = ir.types.iter().find(|t| t.name == name);
        if found.is_none() {
            self.missing(at, "type", name, ir.types.iter().map(|t| t.name.as_str()));
        }
        found
    }

    fn field(&mut self, at: &str, ty: &'a Type, name: &str) -> Option<&'a Field> {
        let found = ty.fields.iter().find(|f| f.name == name);
        if found.is_none() {
            let what = format!("field on type `{}`:", ty.name);
            let names = ty.fields.iter().map(|f| f.name.as_str());
            self.missing(at, &what, name, names);
        }
        found
    }

    fn method(&mut self, at: &str, name: &str) -> Option<&'a Method> {
        let ir = self.ir;
        let found = ir.methods.iter().find(|m| m.name == name);
        if found.is_none() {
            self.missing(
                at,
                "method",
                name,
                ir.methods.iter().map(|m| m.name.as_str()),
            );
        }
        found
    }

    fn param(&mut self, at: &str, method: &'a Method, name: &str) -> Option<&'a Param> {
        let found = method.params.iter().find(|p| p.name == name);
        if found.is_none() {
            let what = format!("param of method `{}`:", method.name);
            let names = method.params.iter().map(|p| p.name.as_str());
            self.missing(at, &what, name, names);
        }
        found
    }

    fn union(&mut self, at: &str, name: &str) -> Option<&'a crate::ir::Union> {
        let ir = self.ir;
        let found = ir.unions.iter().find(|u| u.name == name);
        if found.is_none() {
            self.missing(at, "union", name, ir.unions.iter().map(|u| u.name.as_str()));
        }
        found
    }

    /// A type, union or enum of the IR, or an enum the overlay defines.
    fn entity(&mut self, at: &str, name: &str) {
        let ir = self.ir;
        let names = || {
            ir.types
                .iter()
                .map(|t| t.name.as_str())
                .chain(ir.unions.iter().map(|u| u.name.as_str()))
                .chain(ir.enums.iter().map(|e| e.name.as_str()))
                .chain(self.overlay.enums.keys().map(String::as_str))
        };
        if !names().any(|n| n == name) {
            let candidates: Vec<&str> = names().collect();
            self.missing(at, "type, union or enum", name, candidates.into_iter());
        }
    }

    fn identifier(&mut self, at: &str, name: &str) {
        if !is_identifier(name) || KEYWORDS.contains(&name) {
            self.fail(
                at,
                format!("`{name}` is not a Python identifier (or is a keyword)"),
            );
        }
    }

    fn upper_snake(&mut self, at: &str, name: &str) {
        let mut chars = name.chars();
        let ok = chars.next().is_some_and(|c| c.is_ascii_uppercase())
            && chars.all(|c| c.is_ascii_uppercase() || c.is_ascii_digit() || c == '_');
        if !ok {
            self.fail(at, format!("`{name}` must be UPPER_SNAKE_CASE"));
        }
    }

    /// `<Type>.<field>` / `<method>.<param>` maps (`names`, `defaults`).
    fn member_maps(&mut self, types: &Map<Map<String>>, methods: &Map<Map<String>>) {
        for (t, fields) in types {
            let at = format!("types.{t}");
            let Some(ty) = self.ty(&at, t) else { continue };
            for (f, value) in fields {
                let at = format!("{at}.{f}");
                self.field(&at, ty, f);
                self.identifier(&at, value);
            }
        }
        for (m, params) in methods {
            let at = format!("methods.{m}");
            let Some(method) = self.method(&at, m) else {
                continue;
            };
            for (p, value) in params {
                let at = format!("{at}.{p}");
                self.param(&at, method, p);
                self.identifier(&at, value);
            }
        }
    }

    fn names(&mut self) {
        self.at("names.toml");
        let names = &self.overlay.names;
        self.member_maps(&names.types, &names.methods);
        let ir = self.ir;
        for (t, renames) in &names.types {
            if let Some(ty) = ir.types.iter().find(|x| &x.name == t) {
                let wire = ty.fields.iter().map(|f| f.name.as_str());
                self.unique_names(&format!("types.{t}"), wire, renames);
            }
        }
        for (m, renames) in &names.methods {
            if let Some(method) = ir.methods.iter().find(|x| &x.name == m) {
                let wire = method.params.iter().map(|p| p.name.as_str());
                self.unique_names(&format!("methods.{m}"), wire, renames);
            }
        }
        for (m, params) in &names.union_aliases {
            let at = format!("union_aliases.{m}");
            let Some(method) = self.method(&at, m) else {
                continue;
            };
            for (p, alias) in params {
                let at = format!("{at}.{p}");
                self.param(&at, method, p);
                self.identifier(&at, alias);
            }
        }
    }

    /// After the renames, no two fields (params) share a Python name.
    fn unique_names<'w>(
        &mut self,
        at: &str,
        wire: impl Iterator<Item = &'w str>,
        renames: &Map<String>,
    ) {
        let mut taken: Map<&str> = Map::new();
        for w in wire {
            let py = renames.get(w).map_or(w, String::as_str);
            if let Some(other) = taken.insert(py.to_owned(), w) {
                // report it at the renamed key, the one the overlay author controls
                let (key, with) = if renames.contains_key(w) {
                    (w, other)
                } else {
                    (other, w)
                };
                self.fail(
                    format!("{at}.{key}"),
                    format!("Python name `{py}` is also the name of `{with}`"),
                );
            }
        }
    }

    fn enums(&mut self) {
        for (name, def) in &self.overlay.enums {
            self.at(&format!("enums/{name}.toml"));
            self.identifier(".", name);
            if def.parse.is_none()
                && def.multi_parse.is_none()
                && def.static_members.as_ref().is_none_or(Map::is_empty)
                && def.extract.is_none()
            {
                self.fail(
                    ".",
                    "needs at least one of `parse`, `multi_parse`, `static`, `extract`",
                );
            }
            if let Some(parse) = &def.parse {
                match (&parse.ty, &parse.method) {
                    (Some(t), None) => {
                        if let Some(ty) = self.ty("parse.type", t) {
                            self.field("parse.field", ty, &parse.field);
                        }
                    }
                    (None, Some(m)) => {
                        if let Some(method) = self.method("parse.method", m) {
                            self.param("parse.field", method, &parse.field);
                        }
                    }
                    _ => self.fail("parse", "needs exactly one of `type`, `method`"),
                }
            }
            if let Some(multi) = &def.multi_parse {
                for (i, t) in multi.types.iter().enumerate() {
                    let at = format!("multi_parse.types[{i}]");
                    if let Some(ty) = self.ty(&at, t) {
                        self.field(&at, ty, &multi.field);
                    }
                }
            }
            if let Some(members) = &def.static_members {
                for member in members.keys() {
                    self.upper_snake(&format!("static.{member}"), member);
                }
            }
            if let Some(extract) = &def.extract
                && let Some(ty) = self.ty("extract.type", &extract.ty)
            {
                for (i, f) in extract.exclude.iter().enumerate() {
                    self.field(&format!("extract.exclude[{i}]"), ty, f);
                }
            }
        }
    }

    /// `datetime.toml` / `display.toml`: each field / param exists and its type passes `holds`.
    fn refs(&mut self, file: &str, refs: &Refs, (kind, holds): (&str, fn(&TypeRef) -> bool)) {
        self.at(file);
        for (t, fields) in &refs.types {
            let at = format!("types.{t}");
            let Some(ty) = self.ty(&at, t) else { continue };
            for (i, f) in fields.iter().enumerate() {
                let at = format!("{at}[{i}]");
                if let Some(field) = self.field(&at, ty, f)
                    && !holds(&field.ty.value)
                {
                    self.fail(at, format!("`{t}.{f}` is not {kind} field"));
                }
            }
        }
        for (m, params) in &refs.methods {
            let at = format!("methods.{m}");
            let Some(method) = self.method(&at, m) else {
                continue;
            };
            for (i, p) in params.iter().enumerate() {
                let at = format!("{at}[{i}]");
                if let Some(param) = self.param(&at, method, p)
                    && !holds(&param.ty.value)
                {
                    self.fail(at, format!("`{m}.{p}` is not {kind} param"));
                }
            }
        }
    }

    fn defaults(&mut self) {
        self.at("defaults.toml");
        let defaults = &self.overlay.defaults;
        self.member_maps(&defaults.types, &defaults.methods);
    }

    fn fill_keys(&mut self, at: &str, method: &'a Method, fill: &Map<Fill>) {
        for p in fill.keys() {
            self.param(&format!("{at}.{p}"), method, p);
        }
    }

    fn shortcuts(&mut self) {
        for (t, shortcuts) in &self.overlay.shortcuts {
            self.at(&format!("shortcuts/{t}.toml"));
            self.ty(".", t);
            for (name, s) in shortcuts {
                // the table key becomes a method name on the generated type
                self.identifier(name, name);
                if s.handwritten {
                    let configured = s.method.is_some()
                        || !s.fill.is_empty()
                        || !s.ignore.is_empty()
                        || !s.require.is_empty()
                        || !s.forbid.is_empty();
                    if configured {
                        let message = "`handwritten = true` takes no `method`, `fill`, `ignore`, `require` or `forbid`";
                        self.fail(name.as_str(), message);
                    }
                    continue;
                }
                let Some(m) = &s.method else {
                    self.fail(name.as_str(), "needs `method` (or `handwritten = true`)");
                    continue;
                };
                let Some(method) = self.method(&format!("{name}.method"), m) else {
                    continue;
                };
                self.fill_keys(&format!("{name}.fill"), method, &s.fill);
                for (i, p) in s.ignore.iter().enumerate() {
                    let at = format!("{name}.ignore[{i}]");
                    self.param(&at, method, p);
                    if s.fill.contains_key(p) {
                        self.fail(at, format!("`{p}` is both filled and ignored"));
                    }
                }
            }
        }
    }

    fn unions(&mut self) {
        self.at("unions.toml");
        for (name, rule) in &self.overlay.unions {
            let Some(union) = self.union(name, name) else {
                continue;
            };
            match (&rule.tag, rule.rules.is_empty()) {
                (Some(tag), true) => {
                    for member in &union.members.value {
                        if let Some(ty) = self.ty(&format!("{name}.tag"), member) {
                            self.field(&format!("{name}.tag"), ty, tag);
                        }
                    }
                }
                (None, false) => {}
                _ => self.fail(name.as_str(), "needs exactly one of `tag`, `rules`"),
            }
            for (i, r) in rule.rules.iter().enumerate() {
                let at = format!("{name}.rules[{i}]");
                if !union.members.value.contains(&r.member) {
                    let members = union.members.value.iter().map(String::as_str);
                    self.missing(format!("{at}.member"), "member", &r.member, members);
                } else if r.absent {
                    // a member is often picked by the absence of a field only another member has
                    self.member_field(&format!("{at}.field"), union, &r.field);
                } else if let Some(ty) = self.ty(&at, &r.member) {
                    self.field(&format!("{at}.field"), ty, &r.field);
                }
                let tests = [r.eq.is_some(), r.ne.is_some(), r.present, r.absent];
                if tests.iter().filter(|t| **t).count() != 1 {
                    self.fail(
                        at,
                        "needs exactly one of `eq`, `ne`, `present = true`, `absent = true`",
                    );
                }
            }
        }
    }

    /// `name` is a field of at least one member type of `union`.
    fn member_field(&mut self, at: &str, union: &'a crate::ir::Union, name: &str) {
        let ir = self.ir;
        let fields: Vec<&str> = ir
            .types
            .iter()
            .filter(|t| union.members.value.contains(&t.name))
            .flat_map(|t| t.fields.iter().map(|f| f.name.as_str()))
            .collect();
        if !fields.contains(&name) {
            let what = format!("field on any member of `{}`:", union.name);
            self.missing(at, &what, name, fields.into_iter());
        }
    }

    fn twins(&mut self) {
        self.at("twins.toml");
        for (t, twin) in &self.overlay.twins {
            let output = self.ty(t, t);
            let input = self.ty(t, &format!("Input{t}"));
            let (Some(output), Some(input)) = (output, input) else {
                continue;
            };
            for f in twin.required.keys() {
                let on = |ty: &Type| ty.fields.iter().any(|x| &x.name == f);
                if !on(output) && !on(input) {
                    self.field(&format!("{t}.required.{f}"), output, f);
                }
            }
        }
    }

    fn layout(&mut self) {
        self.at("layout.toml");
        for (t, layout) in &self.overlay.layout {
            let Some(ty) = self.ty(t, t) else { continue };
            for (i, f) in layout.hot.iter().enumerate() {
                self.field(&format!("{t}.hot[{i}]"), ty, f);
            }
        }
    }

    fn type_ref(&mut self, at: &str, r: &TypeRef) {
        match r {
            TypeRef::Prim(_) => {}
            TypeRef::Ref(name) => self.entity(at, name),
            TypeRef::Array(inner) => self.type_ref(at, inner),
            TypeRef::Union(items) => items.iter().for_each(|i| self.type_ref(at, i)),
        }
    }

    fn heuristics(&mut self) {
        self.at("heuristics.toml");
        let h = &self.overlay.heuristics;
        for (m, returns) in &h.returns {
            let at = format!("returns.{m}");
            self.method(&at, m);
            self.type_ref(&at, returns);
        }
        for (t, fields) in &h.consts {
            let at = format!("consts.{t}");
            let Some(ty) = self.ty(&at, t) else { continue };
            for f in fields.keys() {
                self.field(&format!("{at}.{f}"), ty, f);
            }
        }
        for (u, members) in &h.subtypes {
            let at = format!("subtypes.{u}");
            self.union(&at, u);
            for (i, member) in members.iter().enumerate() {
                self.ty(&format!("{at}[{i}]"), member);
            }
        }
        for e in h.enum_members.keys() {
            let ir = self.ir;
            let known = ir.enums.iter().any(|x| &x.name == e) || self.overlay.enums.contains_key(e);
            if !known {
                let names = ir
                    .enums
                    .iter()
                    .map(|x| x.name.as_str())
                    .chain(self.overlay.enums.keys().map(String::as_str));
                let names: Vec<&str> = names.collect();
                self.missing(format!("enum_members.{e}"), "enum", e, names.into_iter());
            }
        }
    }

    fn docs(&mut self) {
        self.at("docs.toml");
        for t in self.overlay.docs.types.keys() {
            self.ty(&format!("types.{t}"), t);
        }
        for m in self.overlay.docs.methods.keys() {
            self.method(&format!("methods.{m}"), m);
        }
    }

    fn methods(&mut self) {
        self.at("methods.toml");
        let methods = &self.overlay.methods;
        for m in methods.idempotent.keys() {
            self.method(&format!("idempotent.{m}"), m);
        }
        for (i, m) in methods.excluded.iter().enumerate() {
            let at = format!("excluded[{i}]");
            self.method(&at, m);
            if methods.idempotent.contains_key(m) {
                self.fail(at, format!("`{m}` is also in `idempotent`; pick one"));
            }
        }
    }

    fn content(&mut self) {
        self.at("content.toml");
        let mut seen = BTreeSet::new();
        for (i, kind) in self.overlay.content.kind.iter().enumerate() {
            let at = format!("kind[{i}]");
            if !seen.insert(kind.name.as_str()) {
                self.fail(
                    format!("{at}.name"),
                    format!("duplicate content kind `{}`", kind.name),
                );
            }
            if let Some(message) = self.ty(&format!("{at}.field"), "Message") {
                self.field(&format!("{at}.field"), message, &kind.field);
            }
            if let Some(copy) = &kind.copy
                && let Some(method) = self.method(&format!("{at}.copy.method"), &copy.method)
            {
                self.fill_keys(&format!("{at}.copy.fill"), method, &copy.fill);
            }
        }
    }

    fn events(&mut self) {
        self.at("events.toml");
        let ir = self.ir;
        let update_types: Vec<&str> = ir
            .types
            .iter()
            .find(|t| t.name == "Update")
            .map(|t| {
                t.fields
                    .iter()
                    .map(|f| f.name.as_str())
                    .filter(|n| *n != "update_id")
                    .collect()
            })
            .unwrap_or_default();
        for name in self.overlay.events.keys() {
            if !update_types.contains(&name.as_str()) {
                self.missing(
                    name.as_str(),
                    "update type",
                    name,
                    update_types.iter().copied(),
                );
            }
        }
    }

    fn bases(&mut self) {
        self.at("bases.toml");
        for (t, bases) in &self.overlay.bases {
            self.ty(t, t);
            for (i, base) in bases.iter().enumerate() {
                let at = format!("{t}[{i}]");
                if base == "MutableTelegramObject" {
                    self.fail(
                        at,
                        "`MutableTelegramObject` is not allowed: all types are immutable (D15)",
                    );
                } else {
                    self.ty(&at, base);
                }
            }
        }
    }

    fn errors(&mut self) {
        self.at("errors.toml");
        let ir = self.ir;
        // an html-only build without errors.json has nothing to check the pins against
        let checked = ir.header.sources.contains(&Source::Errors);
        let mut seen: Map<&str> = Map::new();
        for (message, name) in &self.overlay.errors.names {
            let at = format!("names.{message}");
            if checked && !ir.errors.iter().any(|e| &e.message == message) {
                let messages = ir.errors.iter().map(|e| e.message.as_str());
                self.missing(at.as_str(), "errors.json message", message, messages);
            }
            self.upper_snake(&at, name);
            if let Some(first) = seen.insert(name.clone(), message.as_str()) {
                self.fail(at, format!("`{name}` is also the name of `{first}`"));
            }
        }
    }
}

fn is_identifier(name: &str) -> bool {
    let mut chars = name.chars();
    chars
        .next()
        .is_some_and(|c| c.is_ascii_alphabetic() || c == '_')
        && chars.all(|c| c.is_ascii_alphanumeric() || c == '_')
}

fn holds_integer(r: &TypeRef) -> bool {
    match r {
        TypeRef::Prim(p) => matches!(p, Prim::Int | Prim::Int32 | Prim::Int64),
        TypeRef::Union(items) => items.iter().any(holds_integer),
        TypeRef::Ref(_) | TypeRef::Array(_) => false,
    }
}

fn holds_string(r: &TypeRef) -> bool {
    match r {
        TypeRef::Prim(p) => *p == Prim::String,
        TypeRef::Ref(_) => false,
        TypeRef::Array(inner) => holds_string(inner),
        TypeRef::Union(items) => items.iter().any(holds_string),
    }
}

/// The candidate within edit distance `max(2, len / 3)` of `name`, nearest first, ties by name.
fn closest<'n>(name: &str, candidates: impl Iterator<Item = &'n str>) -> Option<&'n str> {
    let limit = (name.chars().count() / 3).max(2);
    candidates
        .map(|c| (levenshtein(name, c), c))
        .filter(|(d, _)| *d <= limit)
        .min()
        .map(|(_, c)| c)
}

fn levenshtein(a: &str, b: &str) -> usize {
    let b: Vec<char> = b.chars().collect();
    let mut row: Vec<usize> = (0..=b.len()).collect();
    for (i, ca) in a.chars().enumerate() {
        let mut prev = row[0];
        row[0] = i + 1;
        for (j, cb) in b.iter().enumerate() {
            let cur = row[j + 1];
            row[j + 1] = (prev + usize::from(ca != *cb)).min(row[j] + 1).min(cur + 1);
            prev = cur;
        }
    }
    row[b.len()]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn levenshtein_distances() {
        assert_eq!(levenshtein("", "abc"), 3);
        assert_eq!(levenshtein("edit_dat", "edit_date"), 1);
        assert_eq!(levenshtein("kitten", "sitting"), 3);
    }

    #[test]
    fn closest_respects_the_limit() {
        let names = ["date", "edit_date", "chat"];
        assert_eq!(closest("edit_dat", names.into_iter()), Some("edit_date"));
        assert_eq!(closest("zzzzzzzz", names.into_iter()), None);
    }
}
