//! Per-type field tables: data that C-18 emits, read by the shared [`Cursor`](super::Cursor).

/// What a field holds. Metadata for the debug walks and the generator; decoding itself goes
/// through the type's `set`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Kind {
    Bool,
    I32,
    I64,
    F64,
    Str,
    /// a small enum-like string, see [`IStr`](super::IStr)
    IStr,
    UnixTime,
    Enum,
    Object,
    Array,
    /// kept as a raw range (fields outside the decoded set)
    Opaque,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct Field {
    /// the wire name; the key of the JSON path in errors
    pub(crate) wire: &'static str,
    pub(crate) kind: Kind,
    pub(crate) required: bool,
    /// stored out of line (boxed cold struct or sorted cold vec)
    pub(crate) cold: bool,
}

/// The decode table of one type.
#[derive(Debug)]
pub(crate) struct Table {
    /// indexed by field id
    pub(crate) fields: &'static [Field],
    /// accepted input names, sorted bytewise: every wire name and every Python alias
    /// (`from_user` next to `from`), both under the field's id (owner, B-03 Q2)
    pub(crate) keys: &'static [(&'static str, u16)],
}

impl Table {
    pub(crate) fn lookup(&self, key: &[u8]) -> Option<u16> {
        self.keys
            .binary_search_by(|(name, _)| name.as_bytes().cmp(key))
            .ok()
            .and_then(|index| self.keys.get(index))
            .map(|(_, id)| *id)
    }

    /// The wire name of field `id`, for error paths.
    pub(crate) fn wire(&self, id: u16) -> &'static str {
        self.fields
            .get(usize::from(id))
            .map_or("?", |field| field.wire)
    }
}
