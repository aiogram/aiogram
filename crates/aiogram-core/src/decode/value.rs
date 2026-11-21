//! Value kinds and per-object storage that are not plain Rust scalars.

use super::cursor::Cursor;
use super::error::{DecodeError, DecodeResult};

/// A byte range into the owning update's buffer (the view holds that `Arc<[u8]>`, B-05).
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(crate) struct Raw {
    pub(crate) start: u32,
    pub(crate) end: u32,
}

impl Raw {
    /// The bytes of the range in `buf` (the update's buffer), `None` if it is not that buffer.
    pub(crate) fn slice(self, buf: &[u8]) -> Option<&[u8]> {
        buf.get(self.start as usize..self.end as usize)
    }
}

/// A key the type's table does not know: kept as raw ranges, not decoded (10 Layer 2).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct Unknown {
    /// the key's bytes between the quotes, escapes not decoded
    pub(crate) key: Raw,
    /// the whole JSON value
    pub(crate) value: Raw,
}

/// Header of every decoded object. `B` is the present bitset, `[u64; ceil(fields / 64)]`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct Meta<B> {
    /// the object's own bytes, `{` to `}` (`.raw` / `.raw_json`, D10)
    pub(crate) span: Raw,
    /// fields set in the input, by field id, `null` included (`exclude_unset`, R06)
    pub(crate) present: B,
    /// in input order, duplicates included; empty allocates nothing
    pub(crate) unknown: Box<[Unknown]>,
}

impl<B: AsRef<[u64]>> Meta<B> {
    pub(crate) fn is_set(&self, id: u16) -> bool {
        bit(self.present.as_ref(), id)
    }
}

pub(crate) fn bit(bits: &[u64], id: u16) -> bool {
    bits.get(usize::from(id / 64))
        .is_some_and(|word| word & (1 << (id % 64)) != 0)
}

pub(crate) fn set_bit(bits: &mut [u64], id: u16) {
    if let Some(word) = bits.get_mut(usize::from(id / 64)) {
        *word |= 1 << (id % 64);
    }
}

/// `v` of the required field `field` of the object at `span`.
pub(crate) fn required<T>(v: Option<T>, field: &'static str, span: Raw) -> DecodeResult<T> {
    v.ok_or_else(|| DecodeError::missing(field, span.start))
}

/// A Unix-time field: seconds, UTC (B-05 exposes it as an aware `datetime`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct UnixTime(pub(crate) i64);

/// A small enum-like string: a value of [`INTERNED`] costs no allocation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum IStr {
    Known(&'static str),
    Owned(Box<str>),
}

impl IStr {
    pub(crate) fn as_str(&self) -> &str {
        match self {
            Self::Known(value) => value,
            Self::Owned(value) => value,
        }
    }

    pub(crate) fn new(value: &str) -> Self {
        match INTERNED.binary_search_by(|known| (*known).cmp(value)) {
            Ok(index) => INTERNED
                .get(index)
                .map_or_else(|| Self::Owned(value.into()), |known| Self::Known(known)),
            Err(_) => Self::Owned(value.into()),
        }
    }
}

/// The process-wide intern table: sorted, fixed at build time, so no lock and no growth from
/// untrusted input (owner, B-03 Q3).
// ponytail: seed list (the corpus' language codes and common MIME types); C-18 generates the
// real one from the overlay's enum-like string fields
pub(crate) static INTERNED: &[&str] = &[
    "application/pdf",
    "audio/mpeg",
    "audio/ogg",
    "de",
    "en",
    "es",
    "fr",
    "image/jpeg",
    "image/png",
    "image/webp",
    "it",
    "pt-br",
    "ru",
    "uk",
    "video/mp4",
];

/// A wire enum: known values are variants, anything else is `Unknown(Box<str>)` (10 Layer 1).
pub(crate) trait WireEnum: Sized + Clone + 'static {
    /// wire values, sorted
    const NAMES: &'static [&'static str];
    /// the variant of each of `NAMES`, same order
    const KNOWN: &'static [Self];

    fn unknown(value: Box<str>) -> Self;

    /// Reads a value: a known variant, or `Unknown` with the string.
    fn read(c: &mut Cursor<'_>) -> DecodeResult<Self> {
        Ok(match c.choice(Self::NAMES)? {
            Ok(index) => match Self::KNOWN.get(index) {
                Some(known) => known.clone(),
                // `NAMES` and `KNOWN` out of step: a table bug, kept decodable
                None => Self::unknown(Self::NAMES.get(index).copied().unwrap_or_default().into()),
            },
            Err(value) => Self::unknown(value),
        })
    }
}

/// One entry of a wide type's sorted cold vec: an enum whose variants are the cold fields.
pub(crate) trait ColdField {
    fn id(&self) -> u16;
}

/// Sets field `id` of a cold vec; `None` (a `null`) clears it. Last write wins.
// ponytail: linear `retain` per cold field, O(n²) in the cold fields of one object (≤ 130,
// ~30 in practice); a present-bit check before the scan if it ever shows in a profile
pub(crate) fn cold_set<T: ColdField>(cold: &mut Vec<T>, id: u16, value: Option<T>) {
    cold.retain(|field| field.id() != id);
    cold.extend(value);
}

/// The cold vec of a finished object, sorted by field id.
pub(crate) fn cold_finish<T: ColdField>(mut cold: Vec<T>) -> Box<[T]> {
    cold.sort_unstable_by_key(T::id);
    cold.into_boxed_slice()
}

pub(crate) fn cold_get<T: ColdField>(cold: &[T], id: u16) -> Option<&T> {
    cold.binary_search_by_key(&id, T::id)
        .ok()
        .and_then(|index| cold.get(index))
}
