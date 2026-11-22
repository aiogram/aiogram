//! Fill-DSL (C-07): the text of `overlay/shortcuts/*.toml` fills and guards and of `overlay/events.toml`, parsed and
//! resolved against the IR into [`Ir::shortcuts`] and [`Ir::events`].
//!
//! ```text
//! expr  := path | "self." ident "()" | "None"
//! when  := path                        (truthiness; false omits the param)
//! path  := "self." ident (("." | "?.") ident)*
//! ident := [A-Za-z_][A-Za-z0-9_]*      (a Python name, after the `names.toml` renames)
//! ```
//! No whitespace, no other literal. A guard path takes no `?.`.

use std::collections::BTreeMap;
use std::fmt::Write as _;
use std::path::PathBuf;

use crate::Error;
use crate::ir::{
    EventContext, Field, FillValue, Filled, Guard, Ir, Method, Prim, Shortcut, Step, Type, TypeRef,
};
use crate::overlay::Overlay;
use crate::overlay::check::closest;
use crate::overlay::schema::Fill;

/// A syntax error; `column` is 1-based, in characters of the expression text.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Syntax {
    pub column: usize,
    pub message: String,
}

/// One `.name` / `?.name` of a parsed path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Segment {
    pub name: String,
    /// Written `?.`.
    pub chain: bool,
    pub column: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Expr {
    Path(Vec<Segment>),
    Helper { name: String, column: usize },
    None,
}

/// A fill value: a path, `self.<helper>()` or `None`.
pub fn parse_expr(text: &str) -> Result<Expr, Syntax> {
    if text == "None" {
        return Ok(Expr::None);
    }
    let (mut segments, called) = parse(text, true)?;
    Ok(if called {
        Expr::Helper {
            name: segments.remove(0).name,
            column: FIRST,
        }
    } else {
        Expr::Path(segments)
    })
}

/// A `when` or guard path.
pub fn parse_path(text: &str) -> Result<Vec<Segment>, Syntax> {
    parse(text, false).map(|(segments, _)| segments)
}

fn syntax(column: usize, message: impl Into<String>) -> Syntax {
    Syntax {
        column,
        message: message.into(),
    }
}

/// Column of the first name, after `self.`.
const FIRST: usize = 6;

/// The segments, and whether the text ends in `()` (only when `call`; then there is exactly one segment).
fn parse(text: &str, call: bool) -> Result<(Vec<Segment>, bool), Syntax> {
    let Some(rest) = text.strip_prefix("self.") else {
        let expected = if call {
            "expected `self.<field>`, `self.<helper>()` or `None`"
        } else {
            "expected a path, `self.<field>`"
        };
        return Err(syntax(1, expected));
    };
    let chars: Vec<char> = rest.chars().collect();
    let mut segments = Vec::new();
    let mut chain = false;
    let mut i = 0;
    loop {
        let start = i;
        while i < chars.len() && (chars[i] == '_' || chars[i].is_ascii_alphanumeric()) {
            i += 1;
        }
        if i == start || chars[start].is_ascii_digit() {
            return Err(syntax(start + FIRST, "expected a name"));
        }
        segments.push(Segment {
            name: chars[start..i].iter().collect(),
            chain,
            column: start + FIRST,
        });
        match chars.get(i) {
            None => return Ok((segments, false)),
            Some('.') => {
                chain = false;
                i += 1;
            }
            Some('?') if chars.get(i + 1) == Some(&'.') => {
                chain = true;
                i += 2;
            }
            Some('(') if chars.get(i + 1) == Some(&')') => {
                if !call {
                    return Err(syntax(i + FIRST, "a call is not allowed here"));
                }
                if segments.len() > 1 {
                    return Err(syntax(i + FIRST, "only `self.<helper>()` can be called"));
                }
                if i + 2 != chars.len() {
                    return Err(syntax(i + 2 + FIRST, "expected the end after `()`"));
                }
                return Ok((segments, true));
            }
            Some(c) => {
                let message = format!("unexpected `{c}`: expected `.`, `?.`, `()` or the end");
                return Err(syntax(i + FIRST, message));
            }
        }
    }
}

/// wire type -> helper name -> return type of the hand-written zero-argument helpers (`*_ext.pyi`).
pub type Helpers = BTreeMap<String, BTreeMap<String, TypeRef>>;

/// Resolves every shortcut and event context of `overlay` and stores them in `ir`. On error `ir` is unchanged and
/// every error is returned, sorted by file, as `file: key path: message`.
pub fn apply(ir: &mut Ir, overlay: &Overlay, helpers: &Helpers) -> Result<(), Vec<Error>> {
    let mut r = Resolver {
        ir,
        overlay,
        helpers,
        file: PathBuf::new(),
        errors: Vec::new(),
    };
    let shortcuts = r.shortcuts();
    let events = r.events();
    let mut errors = r.errors;
    if !errors.is_empty() {
        errors.sort_by(|a, b| a.0.cmp(&b.0));
        return Err(errors
            .into_iter()
            .map(|(path, at, message)| crate::invalid(&path, (at, message)))
            .collect());
    }
    ir.shortcuts = shortcuts;
    ir.events = events;
    Ok(())
}

/// The type of a resolved value.
struct Val {
    ty: TypeRef,
    nullable: bool,
}

struct Resolver<'a> {
    ir: &'a Ir,
    overlay: &'a Overlay,
    helpers: &'a Helpers,
    file: PathBuf,
    /// `(file, key path, message)`
    errors: Vec<(PathBuf, String, String)>,
}

impl<'a> Resolver<'a> {
    fn at(&mut self, file: &str) {
        self.file = self.overlay.root.join(file);
    }

    fn fail(&mut self, at: &str, message: impl Into<String>) {
        let error = (self.file.clone(), at.to_owned(), message.into());
        self.errors.push(error);
    }

    fn shortcuts(&mut self) -> Vec<Shortcut> {
        let ir = self.ir;
        let mut out = Vec::new();
        for (t, shortcuts) in &self.overlay.shortcuts {
            self.at(&format!("shortcuts/{t}.toml"));
            if !ir.types.iter().any(|x| x.name == *t) {
                self.fail(".", format!("no type `{t}`"));
                continue;
            }
            for (name, s) in shortcuts {
                if s.handwritten {
                    continue;
                }
                let Some(m) = &s.method else {
                    self.fail(name, "needs `method` (or `handwritten = true`)");
                    continue;
                };
                let Some(method) = ir.methods.iter().find(|x| x.name == *m) else {
                    self.fail(&format!("{name}.method"), format!("no method `{m}`"));
                    continue;
                };
                let mut guarded = Vec::new();
                let mut require = Vec::new();
                for (i, g) in s.require.iter().enumerate() {
                    let at = format!("{name}.require[{i}].path");
                    if let Some((path, _)) = self.guard(&at, t, &g.path, &guarded) {
                        guarded.push(path.clone());
                        require.push(Guard {
                            path,
                            message: g.message.clone(),
                        });
                    }
                }
                let mut forbid = Vec::new();
                for (i, g) in s.forbid.iter().enumerate() {
                    let at = format!("{name}.forbid[{i}].path");
                    let Some((path, val)) = self.guard(&at, t, &g.path, &guarded) else {
                        continue;
                    };
                    if !val.nullable {
                        let message = format!(
                            "column 1: `{}` is never None here, so this guard always raises",
                            g.path
                        );
                        self.fail(&at, message);
                    } else {
                        forbid.push(Guard {
                            path,
                            message: g.message.clone(),
                        });
                    }
                }
                for (i, p) in s.ignore.iter().enumerate() {
                    let at = format!("{name}.ignore[{i}]");
                    if self.param(&at, method, p).is_some_and(|x| x.required.value) {
                        let message = format!("`{p}` of `{m}` is required and cannot be ignored");
                        self.fail(&at, message);
                    }
                }
                let mut fill = BTreeMap::new();
                for (p, f) in &s.fill {
                    let at = format!("{name}.fill.{p}");
                    if let Some(filled) = self.argument(&at, t, method, p, f, &guarded) {
                        fill.insert(p.clone(), filled);
                    }
                }
                out.push(Shortcut {
                    ty: t.clone(),
                    name: name.clone(),
                    method: m.clone(),
                    require,
                    forbid,
                    ignore: s.ignore.clone(),
                    fill,
                });
            }
        }
        out
    }

    fn param(&mut self, at: &str, method: &'a Method, name: &str) -> Option<&'a crate::ir::Param> {
        let found = method.params.iter().find(|p| p.name == name);
        if found.is_none() {
            let hint = hint(closest(name, method.params.iter().map(|p| p.name.as_str())));
            let message = format!("`{name}` is not a param of `{}`{hint}", method.name);
            self.fail(at, message);
        }
        found
    }

    fn guard(
        &mut self,
        at: &str,
        root: &str,
        text: &str,
        guarded: &[Vec<Step>],
    ) -> Option<(Vec<Step>, Val)> {
        let segments = match parse_path(text) {
            Ok(s) => s,
            Err(e) => {
                self.syntax(at, &e);
                return None;
            }
        };
        if let Some(s) = segments.iter().find(|s| s.chain) {
            let message = format!("column {}: a guard takes no `?.`", s.column - 2);
            self.fail(at, message);
            return None;
        }
        self.path(at, root, &segments, guarded)
    }

    fn syntax(&mut self, at: &str, e: &Syntax) {
        self.fail(at, format!("column {}: {}", e.column, e.message));
    }

    /// A shortcut fill: the value must exist and be assignable to the param.
    fn argument(
        &mut self,
        at: &str,
        root: &str,
        method: &'a Method,
        name: &str,
        fill: &Fill,
        guarded: &[Vec<Step>],
    ) -> Option<Filled> {
        // the value is resolved even for an unknown param, so one run reports every error
        let param = self.param(at, method, name);
        let (filled, val) = self.fill(at, root, fill, guarded)?;
        let param = param?;
        let at = if fill.when.is_some() {
            format!("{at}.expr")
        } else {
            at.to_owned()
        };
        let target = format!("`{name}` of `{}`", method.name);
        let required = param.required.value;
        match val {
            None if required => {
                self.fail(
                    &at,
                    format!("column 1: {target} is required and cannot be `None`"),
                );
                return None;
            }
            None => {}
            Some(v) => {
                if !assignable(self.ir, &v.ty, &param.ty.value) {
                    let message = format!(
                        "column 1: the value is `{}` and cannot fill {target} (`{}`)",
                        show(&v.ty),
                        show(&param.ty.value)
                    );
                    self.fail(&at, message);
                    return None;
                }
                if required && (v.nullable || filled.when.is_some()) {
                    let why = if filled.when.is_some() {
                        "its `when` can omit it"
                    } else {
                        "the value may be None"
                    };
                    self.fail(&at, format!("column 1: {target} is required, but {why}"));
                    return None;
                }
            }
        }
        Some(filled)
    }

    /// Parses and resolves a fill. The value type is `None` for the `None` literal.
    fn fill(
        &mut self,
        at: &str,
        root: &str,
        fill: &Fill,
        guarded: &[Vec<Step>],
    ) -> Option<(Filled, Option<Val>)> {
        let (expr_at, when) = match &fill.when {
            None => (at.to_owned(), None),
            Some(text) => {
                let when_at = format!("{at}.when");
                let segments = match parse_path(text) {
                    Ok(s) => s,
                    Err(e) => {
                        self.syntax(&when_at, &e);
                        return None;
                    }
                };
                let (steps, _) = self.path(&when_at, root, &segments, guarded)?;
                (format!("{at}.expr"), Some(steps))
            }
        };
        let expr = match parse_expr(&fill.expr) {
            Ok(e) => e,
            Err(e) => {
                self.syntax(&expr_at, &e);
                return None;
            }
        };
        let (value, val) = match expr {
            Expr::None => (FillValue::None, None),
            Expr::Path(segments) => {
                let (steps, val) = self.path(&expr_at, root, &segments, guarded)?;
                (FillValue::Path(steps), Some(val))
            }
            Expr::Helper { name, column } => {
                let declared = self.helpers.get(root);
                let Some(ty) = declared.and_then(|h| h.get(&name)) else {
                    let known = match declared {
                        Some(h) if !h.is_empty() => {
                            let names: Vec<String> = h.keys().map(|k| format!("`{k}`")).collect();
                            format!("known: {}", names.join(", "))
                        }
                        _ => format!("no helpers are declared for `{root}`"),
                    };
                    let message =
                        format!("column {column}: `{root}` has no helper `{name}()` ({known})");
                    self.fail(&expr_at, message);
                    return None;
                };
                let val = Val {
                    ty: ty.clone(),
                    nullable: false,
                };
                (FillValue::Helper(name), Some(val))
            }
        };
        Some((Filled { value, when }, val))
    }

    /// Walks `segments` from `root`. A step after an optional field needs `?.` or a `require` guard on that prefix.
    fn path(
        &mut self,
        at: &str,
        root: &str,
        segments: &[Segment],
        guarded: &[Vec<Step>],
    ) -> Option<(Vec<Step>, Val)> {
        let mut ty = TypeRef::Ref(root.to_owned());
        let mut nullable = false;
        let mut steps: Vec<Step> = Vec::new();
        let mut shown = String::from("self");
        for seg in segments {
            let column = seg.column;
            if nullable && !seg.chain {
                let message = format!(
                    "column {column}: `{shown}` may be None: add a `require` guard or write `?.`"
                );
                self.fail(at, message);
                return None;
            }
            let Some((owner, members)) = self.members(&ty) else {
                let message = format!(
                    "column {column}: `{shown}` is `{}`, which has no fields",
                    show(&ty)
                );
                self.fail(at, message);
                return None;
            };
            let unknown: Vec<String> = members
                .iter()
                .filter_map(|m| m.err())
                .map(|m| format!("`{m}`"))
                .collect();
            if !unknown.is_empty() {
                let message = format!(
                    "column {column}: `{owner}` has members that are not types in the IR: {}",
                    unknown.join(", ")
                );
                self.fail(at, message);
                return None;
            }
            let members: Vec<&Type> = members.into_iter().flatten().collect();
            let found: Vec<Option<&Field>> = members
                .iter()
                .map(|t| t.fields.iter().find(|f| self.py(t, f) == seg.name))
                .collect();
            let present: Vec<&Field> = found.iter().flatten().copied().collect();
            let Some(first) = present.first() else {
                let names = members
                    .iter()
                    .flat_map(|t| t.fields.iter().map(move |f| (t, f)))
                    .map(|(t, f)| self.py(t, f));
                let hint = hint(closest(&seg.name, names));
                let missing = if members.len() == 1 {
                    format!("`{owner}` has no field `{}`", seg.name)
                } else {
                    format!("no member of `{owner}` has a field `{}`", seg.name)
                };
                let message = format!(
                    "column {column}: {missing}{hint}; if it was removed upstream, keep it with a \
                     `removed_field` entry in `butcher/ledger.toml`, or change this path"
                );
                self.fail(at, message);
                return None;
            };
            if present.len() < members.len() && !seg.chain {
                let lacking: Vec<String> = members
                    .iter()
                    .zip(&found)
                    .filter(|(_, f)| f.is_none())
                    .map(|(t, _)| format!("`{}`", t.name))
                    .collect();
                let message = format!(
                    "column {column}: `{}` is not a field of every member of `{owner}` (missing on {}): write `?.`",
                    seg.name,
                    lacking.join(", ")
                );
                self.fail(at, message);
                return None;
            }
            if present.iter().any(|f| f.ty.value != first.ty.value) {
                let message = format!(
                    "column {column}: `{}` has a different type on the members of `{owner}`",
                    seg.name
                );
                self.fail(at, message);
                return None;
            }
            if present.iter().any(|f| f.name != first.name) {
                let wire: Vec<String> = present.iter().map(|f| format!("`{}`", f.name)).collect();
                let message = format!(
                    "column {column}: `{}` is a different wire field on the members of `{owner}` ({}): \
                     one step reads one field",
                    seg.name,
                    wire.join(", ")
                );
                self.fail(at, message);
                return None;
            }
            let optional = present.len() < members.len() || !present.iter().all(|f| is_required(f));
            steps.push(Step {
                field: first.name.clone(),
                chain: seg.chain,
            });
            let _ = write!(shown, "{}{}", if seg.chain { "?." } else { "." }, seg.name);
            let covered = guarded.iter().any(|g| same_fields(g, &steps));
            nullable = nullable || (optional && !covered);
            ty = first.ty.value.clone();
        }
        Some((steps, Val { ty, nullable }))
    }

    /// The object types a value of `ty` can be: one type, or the members of a union (`Err` for a member name that
    /// is not a type).
    fn members(&self, ty: &TypeRef) -> Option<(&'a str, Vec<Result<&'a Type, &'a str>>)> {
        let ir = self.ir;
        let TypeRef::Ref(name) = ty else {
            return None;
        };
        if let Some(t) = ir.types.iter().find(|t| t.name == *name) {
            return Some((&t.name, vec![Ok(t)]));
        }
        let union = ir.unions.iter().find(|u| u.name == *name)?;
        let members = union
            .members
            .value
            .iter()
            .map(|m| ir.types.iter().find(|t| t.name == *m).ok_or(m.as_str()))
            .collect();
        Some((&union.name, members))
    }

    /// The Python name of a field: its `names.toml` rename, else the wire name.
    fn py(&self, ty: &Type, field: &'a Field) -> &'a str {
        let rename = self.overlay.names.types.get(&ty.name);
        rename
            .and_then(|r| r.get(&field.name))
            .map_or(field.name.as_str(), String::as_str)
    }

    fn events(&mut self) -> Vec<EventContext> {
        let ir = self.ir;
        self.at("events.toml");
        let update = ir.types.iter().find(|t| t.name == "Update");
        let mut out = Vec::new();
        for (name, event) in &self.overlay.events {
            let field = update.and_then(|t| t.fields.iter().find(|f| f.name == *name));
            let Some(TypeRef::Ref(root)) = field.map(|f| &f.ty.value) else {
                self.fail(name, format!("no update type `{name}`"));
                continue;
            };
            let user = TypeRef::Ref("User".to_owned());
            let chat = TypeRef::Ref("Chat".to_owned());
            out.push(EventContext {
                update: name.clone(),
                user: self.slot(name, "user", root, event.user.as_ref(), &user),
                chat: self.slot(name, "chat", root, event.chat.as_ref(), &chat),
                thread_id: self.slot(
                    name,
                    "thread_id",
                    root,
                    event.thread_id.as_ref(),
                    &TypeRef::Prim(Prim::Int),
                ),
                business_connection_id: self.slot(
                    name,
                    "business_connection_id",
                    root,
                    event.business_connection_id.as_ref(),
                    &TypeRef::Prim(Prim::String),
                ),
            });
        }
        out
    }

    /// One event-context value: optional by nature, so only its type is checked.
    fn slot(
        &mut self,
        event: &str,
        key: &str,
        root: &str,
        fill: Option<&Fill>,
        expected: &TypeRef,
    ) -> Option<Filled> {
        let fill = fill?;
        let at = format!("{event}.{key}");
        let (filled, val) = self.fill(&at, root, fill, &[])?;
        if let Some(v) = val
            && !assignable(self.ir, &v.ty, expected)
        {
            let at = if fill.when.is_some() {
                format!("{at}.expr")
            } else {
                at
            };
            let message = format!(
                "column 1: the value is `{}` and cannot be the event `{key}` (`{}`)",
                show(&v.ty),
                show(expected)
            );
            self.fail(&at, message);
            return None;
        }
        Some(filled)
    }
}

fn hint(closest: Option<&str>) -> String {
    closest
        .map(|c| format!(" (closest: `{c}`)"))
        .unwrap_or_default()
}

fn is_required(field: &Field) -> bool {
    field.response.as_ref().is_some_and(|u| u.required.value)
}

fn same_fields(a: &[Step], b: &[Step]) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(x, y)| x.field == y.field)
}

/// Whether a value of type `v` can be sent where `p` is expected.
fn assignable(ir: &Ir, v: &TypeRef, p: &TypeRef) -> bool {
    use TypeRef::{Array, Prim as P, Ref, Union};
    let int = |x: &Prim| matches!(x, Prim::Int | Prim::Int32 | Prim::Int64);
    match (v, p) {
        _ if v == p => true,
        (Union(vs), _) => vs.iter().all(|x| assignable(ir, x, p)),
        (_, Union(ps)) => ps.iter().any(|x| assignable(ir, v, x)),
        (P(a), P(b)) => (int(a) && int(b)) || (*a == Prim::True && *b == Prim::Bool),
        (Ref(a), Ref(b)) => ir
            .unions
            .iter()
            .any(|u| u.name == *b && u.members.value.contains(a)),
        (Array(a), Array(b)) => assignable(ir, a, b),
        _ => false,
    }
}

fn show(ty: &TypeRef) -> String {
    match ty {
        TypeRef::Prim(p) => match p {
            Prim::Int => "int",
            Prim::Int32 => "int32",
            Prim::Int64 => "int64",
            Prim::Float => "float",
            Prim::String => "string",
            Prim::Bool => "bool",
            Prim::True => "true",
        }
        .to_owned(),
        TypeRef::Ref(name) => name.clone(),
        TypeRef::Array(inner) => format!("array of {}", show(inner)),
        TypeRef::Union(items) => items.iter().map(show).collect::<Vec<_>>().join(" or "),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn show_names_every_type_form() {
        let prims = [
            Prim::Int,
            Prim::Int32,
            Prim::Int64,
            Prim::Float,
            Prim::String,
            Prim::Bool,
            Prim::True,
        ];
        let names: Vec<String> = prims.into_iter().map(|p| show(&TypeRef::Prim(p))).collect();
        assert_eq!(
            names,
            ["int", "int32", "int64", "float", "string", "bool", "true"]
        );
        let array = TypeRef::Array(Box::new(TypeRef::Ref("PhotoSize".to_owned())));
        assert_eq!(show(&array), "array of PhotoSize");
    }
}
