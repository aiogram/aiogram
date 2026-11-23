//! `butcher/overlay/**/*.toml`: hand-written facts on top of the IR (plan C-06, v4/research/02 §3).
//!
//! [`Overlay::load`] reads the files and rejects unknown keys and unknown files; [`Overlay::check`] checks every
//! reference against the IR. An overlay is valid when both pass. Completeness rules (every method has an
//! `idempotent` decision, every update type an `events.toml` entry, ...) belong to `butcher check` (C-23), so
//! a missing entry or file is not an error here. The layout and every kind are documented in
//! `butcher/overlay/README.md`.

use std::path::{Path, PathBuf};

use serde::de::DeserializeOwned;

use crate::Error;

pub(crate) mod check;
pub mod schema;

use schema::{
    Content, Defaults, Docs, EnumDef, Errors, Event, Heuristics, Layout, Map, Methods, Names, Refs,
    Shortcut, Twin, UnionRule,
};

/// Directories holding one `<Name>.toml` per entity.
pub const DIRS: [&str; 2] = ["enums", "shortcuts"];

#[derive(Debug, Clone, Default, PartialEq)]
pub struct Overlay {
    /// The directory it was loaded from; `check` names files relative to it.
    pub root: PathBuf,
    pub names: Names,
    /// enum name (file stem) -> definition
    pub enums: Map<EnumDef>,
    pub datetime: Refs,
    pub defaults: Defaults,
    /// type (file stem) -> shortcut name -> shortcut
    pub shortcuts: Map<Map<Shortcut>>,
    pub unions: Map<UnionRule>,
    pub twins: Map<Twin>,
    pub layout: Map<Layout>,
    pub heuristics: Heuristics,
    pub docs: Docs,
    pub methods: Methods,
    pub display: Refs,
    pub content: Content,
    pub events: Map<Event>,
    /// type -> secondary bases (D83)
    pub bases: Map<Vec<String>>,
    pub errors: Errors,
}

impl Overlay {
    /// Reads `<dir>/**/*.toml`. A missing file is an empty kind; a file outside the layout is an error.
    pub fn load(dir: &Path) -> Result<Overlay, Error> {
        let mut overlay = Overlay {
            root: dir.to_owned(),
            ..Overlay::default()
        };
        for entry in list(dir)? {
            let name = file_name(&entry);
            if entry.is_dir() && DIRS.contains(&name.as_str()) {
                for file in list(&entry)? {
                    let Some(stem) = toml_stem(&file) else {
                        return Err(stray(&file, "expected `<Name>.toml`"));
                    };
                    if name == "enums" {
                        overlay.enums.insert(stem, parse(&file)?);
                    } else {
                        overlay.shortcuts.insert(stem, parse(&file)?);
                    }
                }
                continue;
            }
            match name.as_str() {
                "README.md" if entry.is_file() => {}
                "names.toml" => overlay.names = parse(&entry)?,
                "datetime.toml" => overlay.datetime = parse(&entry)?,
                "defaults.toml" => overlay.defaults = parse(&entry)?,
                "unions.toml" => overlay.unions = parse(&entry)?,
                "twins.toml" => overlay.twins = parse(&entry)?,
                "layout.toml" => overlay.layout = parse(&entry)?,
                "heuristics.toml" => overlay.heuristics = parse(&entry)?,
                "docs.toml" => overlay.docs = parse(&entry)?,
                "methods.toml" => overlay.methods = parse(&entry)?,
                "display.toml" => overlay.display = parse(&entry)?,
                "content.toml" => overlay.content = parse(&entry)?,
                "events.toml" => overlay.events = parse(&entry)?,
                "bases.toml" => overlay.bases = parse(&entry)?,
                "errors.toml" => overlay.errors = parse(&entry)?,
                _ => {
                    return Err(stray(
                        &entry,
                        "not an overlay file (see butcher/overlay/README.md)",
                    ));
                }
            }
        }
        Ok(overlay)
    }

    /// Every dangling reference or broken rule, sorted by file then key path; empty means valid.
    pub fn check(&self, ir: &crate::ir::Ir) -> Vec<Error> {
        check::check(self, ir)
    }
}

/// sha256 (hex) over the overlay, for `Manifest.overlay_sha256`. Hashes every `*.toml` under `dir`, sorted by its
/// relative path written with `/`: the path, NUL, the byte length, NUL, the bytes. Paths are hashed so a rename
/// changes the digest; `README.md` is docs and is not hashed.
pub fn digest(dir: &Path) -> Result<String, Error> {
    let mut files = Vec::new();
    collect(dir, "", &mut files)?;
    files.sort();
    let mut buf = Vec::new();
    for (rel, path) in files {
        let bytes = std::fs::read(&path).map_err(|source| Error::Io { path, source })?;
        buf.extend_from_slice(format!("{rel}\0{}\0", bytes.len()).as_bytes());
        buf.extend_from_slice(&bytes);
    }
    Ok(crate::fetch::sha256(&buf))
}

fn collect(dir: &Path, prefix: &str, out: &mut Vec<(String, PathBuf)>) -> Result<(), Error> {
    for entry in list(dir)? {
        let rel = format!("{prefix}{}", file_name(&entry));
        if entry.is_dir() {
            collect(&entry, &format!("{rel}/"), out)?;
        } else if rel.ends_with(".toml") {
            out.push((rel, entry));
        }
    }
    Ok(())
}

/// Directory entries except dot-files, sorted so errors and load order do not depend on the file system.
fn list(dir: &Path) -> Result<Vec<PathBuf>, Error> {
    let io = |source| Error::Io {
        path: dir.to_owned(),
        source,
    };
    let mut entries = Vec::new();
    for entry in std::fs::read_dir(dir).map_err(io)? {
        let path = entry.map_err(io)?.path();
        // `.DS_Store`, `.gitkeep`, editor swap files: never overlay data
        if !file_name(&path).starts_with('.') {
            entries.push(path);
        }
    }
    entries.sort();
    Ok(entries)
}

fn file_name(path: &Path) -> String {
    path.file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default()
}

fn toml_stem(path: &Path) -> Option<String> {
    let name = file_name(path);
    let stem = name.strip_suffix(".toml")?;
    (path.is_file() && !stem.is_empty()).then(|| stem.to_owned())
}

fn stray(path: &Path, message: &str) -> Error {
    crate::invalid(path, (".".to_owned(), message.to_owned()))
}

fn parse<T: DeserializeOwned>(path: &Path) -> Result<T, Error> {
    let text = crate::read(path)?;
    // a syntax error keeps toml's whole message: it carries the line and column
    let de = toml::Deserializer::parse(&text)
        .map_err(|e| crate::invalid(path, (".".to_owned(), e.to_string().trim_end().to_owned())))?;
    serde_path_to_error::deserialize(de).map_err(|e| {
        // toml prefixes a source snippet; the key path already says where, keep the last line ("unknown field ...")
        let inner = e.inner().to_string();
        let message = inner
            .trim_end()
            .lines()
            .last()
            .unwrap_or_default()
            .to_owned();
        crate::invalid(path, (e.path().to_string(), message))
    })
}
