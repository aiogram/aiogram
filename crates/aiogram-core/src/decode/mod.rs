//! The class-independent decode core of the Telegram types (B-03): JSON bytes go straight to
//! Rust structs in one jiter pass, with no Python objects and no intermediate tree (01 §3.1).
//!
//! A type implements [`Decode`]: a field [`Table`] (data), a `Partial` of `Option` locals, a
//! `set` with one arm per field and a `finish` that builds `Self` from the locals (13 B1, B20).
//! The loop is the trait's own `decode`, so per-type code has `Self` = the type and nothing is
//! instantiated per caller (08 §7 items 12-13); key lookup, unknown keys and present bits live
//! in the shared, non-generic [`Cursor`] (B21).
//!
//! Input rules: duplicate keys, last wins (as `json.loads`); a wire name and its Python alias
//! (`from` / `from_user`) are one field, last wins; `null` is "set to `None`"; a lone surrogate
//! escape (`"\ud800"`) anywhere is an error at the nearest known field: jiter rejects it in
//! skipped values too, and Rust `str` cannot hold it (B-14 isolates it, the bytes stay).
//!
//! Not wired into anything yet (PD-03): B-04 implements it for the spike types.
#![cfg_attr(not(test), allow(dead_code, unused_imports))]

mod cursor;
mod error;
mod table;
mod value;

#[cfg(test)]
mod tests;

pub(crate) use cursor::Cursor;
pub(crate) use error::{DecodeError, DecodeResult, ErrorKind, Seg};
pub(crate) use table::{Field, Kind, Table};
pub(crate) use value::{
    ColdField, INTERNED, IStr, Meta, Raw, UnixTime, WireEnum, bit, cold_finish, cold_get, cold_set,
    required,
};

/// A decodable type. `Self` is the type (08 §7 item 13): implement the four items, never
/// override `decode`.
pub(crate) trait Decode: Sized {
    const TABLE: &'static Table;
    /// one `Option` per field (plus the cold vec of a wide type), bound to locals by `finish`
    type Partial: Default;
    /// the present bitset, `[u64; ceil(TABLE.fields.len() / 64)]`
    type Bits: Default + AsRef<[u64]> + AsMut<[u64]>;

    /// Reads field `id` from `c` into `p`: one arm per field, each one `Cursor` call.
    fn set(p: &mut Self::Partial, id: u16, c: &mut Cursor<'_>) -> DecodeResult<()>;

    /// Checks the required fields and builds `Self`.
    fn finish(p: Self::Partial, meta: Meta<Self::Bits>) -> DecodeResult<Self>;

    /// Decodes one JSON object at the cursor. Re-entrant (all state is on the cursor and the
    /// stack), so B-14's stack guard wraps it as is.
    #[inline(never)]
    fn decode(c: &mut Cursor<'_>) -> DecodeResult<Self> {
        let mut p = Self::Partial::default();
        let mut present = Self::Bits::default();
        let mut object = c.begin()?;
        while let Some(id) = c.field(Self::TABLE, &mut object, present.as_mut())? {
            Self::set(&mut p, id, c).map_err(|e| e.at(Seg::Key(Self::TABLE.wire(id))))?;
        }
        Self::finish(p, object.meta(present))
    }

    /// Decodes `data`, a whole JSON document starting at byte `base` of the update's buffer.
    fn from_slice(data: &[u8], base: u32) -> DecodeResult<Self> {
        let mut c = Cursor::new(data, base)?;
        let value = Self::decode(&mut c)?;
        c.finish()?;
        Ok(value)
    }
}
