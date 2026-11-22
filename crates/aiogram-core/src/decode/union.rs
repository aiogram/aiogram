//! Decoded unions (10 Layer 1, D107, 13 B23): a tagged union selects its variant by the tag's
//! raw value, an undiscriminated one by a predicate over one key's raw value. Anything else
//! becomes the union's `Unknown…` variant: an unknown tag, or a malformed member.

use jiter::Jiter;

use super::Decode;
use super::cursor::{Cursor, Probe};
use super::error::{DecodeError, DecodeResult};
use super::scan;
use super::seen::Site;
use super::value::Raw;

/// The payload of a union's `Unknown…` variant.
#[derive(Debug)]
pub(crate) struct UnknownMember<C> {
    /// the selecting key's value, when it is a JSON string
    pub(crate) tag: Option<Box<str>>,
    /// the fields all variants share; `None` when they do not decode either
    pub(crate) common: Option<C>,
    /// the member's bytes, `{` to `}`
    pub(crate) raw: Raw,
    /// why a member failed to decode (D107), or why its shared fields did; `None` for an unknown
    /// tag whose shared fields decode
    pub(crate) error: Option<DecodeError>,
}

/// A decoded union. `Self` is the union (08 §7 item 13): implement the items, never override
/// `decode`.
pub(crate) trait Union: Sized {
    /// the union's name, for the `Unknown…` hook
    const ENTITY: &'static str;
    /// the key whose raw value selects the variant: the tag, or the predicate's field
    const KEY: &'static str;
    /// the fields all variants share, decoded for `Unknown`
    type Common: Decode;

    /// Decodes the variant that `value` selects (the raw JSON of [`KEY`](Self::KEY), `None` if
    /// absent) from the cursor, which is at the member; `None`: no variant matches.
    ///
    /// A tag is compared as sent, quotes included (`br#""member""#`). A tag sent with escapes
    /// (`"member"`) matches nothing and so is an unknown tag; Telegram never escapes ASCII.
    fn variant(value: Option<&[u8]>, c: &mut Cursor<'_>) -> Option<DecodeResult<Self>>;

    fn unknown(member: UnknownMember<Self::Common>) -> Self;

    /// Decodes one member at the cursor. A depth or strict-mode error propagates, as does a
    /// member whose end cannot be found; every other failure is absorbed as `Unknown` (D107).
    #[inline(never)]
    fn decode(c: &mut Cursor<'_>) -> DecodeResult<Self> {
        let probe = c.probe(Self::KEY)?;
        let value = probe.value.and_then(|raw| c.bytes(raw));
        let error = match Self::variant(value, c) {
            Some(Ok(member)) => return Ok(member),
            Some(Err(e)) if e.is_fatal() => return Err(e),
            Some(Err(e)) => Some(e),
            None => None,
        };
        let (tag, end, error) = unknown_member(c, Self::ENTITY, &probe, value, error)?;
        let common = Self::Common::decode(c);
        c.seek(end);
        let (common, error) = match common {
            Ok(common) => (Some(common), error),
            Err(e) if e.is_fatal() => return Err(e),
            Err(e) => (None, error.or(Some(e))),
        };
        Ok(Self::unknown(UnknownMember {
            tag,
            common,
            raw: Raw {
                start: probe.start,
                end,
            },
            error,
        }))
    }
}

/// The non-generic half of the `Unknown` path: finds the member's end, moves the cursor back to
/// its start and reports it to the hook. Returns the tag, the end and `error` back.
#[cold]
fn unknown_member(
    c: &mut Cursor<'_>,
    entity: &'static str,
    probe: &Probe,
    value: Option<&[u8]>,
    error: Option<DecodeError>,
) -> DecodeResult<(Option<Box<str>>, u32, Option<DecodeError>)> {
    let Some(len) = scan::value_end(c.rest(probe.start), 0) else {
        // unbalanced: nothing to go on after, so the update fails (10 Layer 2)
        return Err(error.unwrap_or_else(|| {
            let mut jiter = Jiter::new(c.rest(probe.start));
            match jiter.next_skip() {
                Err(e) => DecodeError::jiter(e, probe.start),
                // cannot happen: jiter's skip is stricter than the scanner
                Ok(()) => DecodeError::missing(entity, probe.start),
            }
        }));
    };
    let end = probe
        .start
        .saturating_add(u32::try_from(len).unwrap_or(u32::MAX));
    let tag = value
        .filter(|raw| raw.first() == Some(&b'"'))
        .and_then(|raw| Jiter::new(raw).next_str().ok().map(Box::from));
    // no selecting key at all (or no object) is a malformed member, not an unknown tag
    let site = if error.is_some() || value.is_none() {
        Site::Malformed
    } else {
        Site::Tag
    };
    c.seek(probe.start);
    c.report(entity, site, tag.as_deref().unwrap_or_default())?;
    Ok((tag, end, error))
}
