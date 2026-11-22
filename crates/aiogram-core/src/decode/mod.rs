//! The class-independent decode core of the Telegram types (B-03): JSON bytes go straight to
//! Rust structs in one jiter pass, with no Python objects and no intermediate tree (01 §3.1).
//!
//! A type implements [`Decode`]: a field [`Table`] (data), a `Partial` of `Option` locals, a
//! `set` with one arm per field and a `finish` that builds `Self` from the locals (13 B1, B20).
//! The loop is the trait's own `decode`, so per-type code has `Self` = the type and nothing is
//! instantiated per caller (08 §7 items 12-13); key lookup, unknown keys and present bits live
//! in the shared, non-generic [`Cursor`] (B21).
//!
//! Input rules: the input must be UTF-8; duplicate keys, last wins and only the winning
//! occurrence is validated (as `json.loads` + validation); a wire name and its Python alias
//! (`from` / `from_user`) are one field, last wins; `null` is "set to `None`"; a lone surrogate
//! escape (`"\ud800"`) anywhere is an error at the nearest known field: jiter rejects it in
//! skipped values too, and Rust `str` cannot hold it (B-14 isolates it, the bytes stay).
//!
//! On top of the core (B-14): unions ([`Union`]), the depth guard in [`Decode::decode`], the
//! `Unknown…` hook ([`Cursor::report`]) and the response envelope and `getUpdates` batch
//! ([`decode_response`], [`decode_updates`], [`decode_update`]).
//!
//! Not wired into anything yet (PD-03): B-04 implements it for the spike types.
#![cfg_attr(not(test), allow(dead_code, unused_imports))]

mod cursor;
mod envelope;
mod error;
mod scan;
mod seen;
mod table;
mod union;
mod value;

#[cfg(test)]
mod tests;

pub(crate) use cursor::Cursor;
pub(crate) use envelope::{
    ApiError, BodyError, BodyResult, Decoded, Item, Options, Response, UpdateError,
    decode_response, decode_update, decode_updates,
};
pub(crate) use error::{DecodeError, DecodeResult, ErrorKind, MAX_DEPTH};
pub(crate) use seen::{Seen, Site};
pub(crate) use table::{Field, Kind, Table};
pub(crate) use union::{Union, UnknownMember};
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

    /// Unknown keys of this type are reported to the `Unknown…` hook as `(entity, site)`:
    /// `Update` sets it (an unknown key there is an unknown update type).
    const UNKNOWN_KEYS: Option<(&'static str, Site)> = None;

    /// Decodes one JSON object at the cursor, depth-guarded (13 B7, B19): past [`MAX_DEPTH`]
    /// nested objects it is an error, and when the stack runs low it re-enters itself on a
    /// fresh segment through the one non-generic [`grow`], so the body is compiled once.
    #[inline(never)]
    fn decode(c: &mut Cursor<'_>) -> DecodeResult<Self> {
        if low_stack() {
            let mut out = None;
            grow(&mut || out = Some(Self::decode(c)));
            return out.unwrap_or_else(|| Err(DecodeError::new(ErrorKind::Depth, c.mark())));
        }
        c.enter()?;
        let out = Self::object(c);
        c.leave();
        out
    }

    /// The object loop of [`decode`](Self::decode), which callers use instead.
    #[inline]
    fn object(c: &mut Cursor<'_>) -> DecodeResult<Self> {
        let mut p = Self::Partial::default();
        let mut present = Self::Bits::default();
        let mut object = c.begin()?;
        while let Some(id) = c.field(Self::TABLE, &mut object, present.as_mut())? {
            let mark = c.mark();
            match Self::set(&mut p, id, c) {
                Ok(()) => object.settled(id),
                Err(e) => c.recover(Self::TABLE, &mut object, mark, id, e)?,
            }
        }
        if let Some((entity, site)) = Self::UNKNOWN_KEYS {
            c.report_keys(&object, entity, site)?;
        }
        Self::finish(p, object.meta(present)?)
    }

    /// Decodes `data`, a whole JSON document starting at byte `base` of the update's buffer.
    fn from_slice(data: &[u8], base: u32) -> DecodeResult<Self> {
        let mut c = Cursor::new(data, base)?;
        let value = Self::decode(&mut c)?;
        c.finish()?;
        Ok(value)
    }
}

/// Below this much stack left, [`Decode::decode`] continues on a new segment.
const RED_ZONE: usize = 128 * 1024;
/// Size of each new segment.
const STACK_SEGMENT: usize = 1024 * 1024;

fn low_stack() -> bool {
    stacker::remaining_stack().is_some_and(|left| left < RED_ZONE)
}

/// Runs `f` on a new stack segment: the single `stacker` instance (13 B19).
#[inline(never)]
fn grow(f: &mut dyn FnMut()) {
    stacker::grow(STACK_SEGMENT, f);
}
