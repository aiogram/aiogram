//! The response envelope (05 §2.2, 13 B22) and per-update isolation (10 Layer 2, R04).
//!
//! Pure Rust: `&[u8]` in, owned values out, no Python objects. So the caller (B-05 / D-09) can
//! run each entry point inside `py.detach` (07 §2), and logs `first_seen` after it.

use std::sync::Arc;

use super::Decode;
use jiter::Jiter;

use super::cursor::{Cursor, element_utf8};
use super::error::{DecodeError, DecodeResult, ErrorKind, Seg};
use super::scan;
use super::seen::Seen;
use super::table::{Field, Kind, Table};
use super::value::Raw;

/// Per-call decode options.
#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct Options {
    /// `DecodePolicy` "strict": every `Unknown…` is an error (D-09 / E-14 own the switch)
    pub(crate) strict: bool,
}

/// A decoded value plus the first occurrences the `Unknown…` hook counted while decoding it.
#[derive(Debug)]
pub(crate) struct Decoded<T> {
    pub(crate) value: T,
    pub(crate) first_seen: Vec<Seen>,
}

#[derive(Debug)]
pub(crate) enum Response<T> {
    /// `{"ok":true,"result":…}`
    Ok(T),
    /// `{"ok":false,…}`
    Err(ApiError),
}

/// `{"ok":false,…}`, for Python to map onto the exception classes (D-02).
#[derive(Debug)]
pub(crate) struct ApiError {
    /// `Option`, as in 3.x `Response`
    pub(crate) error_code: Option<i64>,
    pub(crate) description: Option<Box<str>>,
    /// raw range in the body (`parameters_raw`)
    pub(crate) parameters: Option<Raw>,
}

/// A body that does not decode.
#[derive(Debug)]
pub(crate) struct BodyError {
    pub(crate) error: DecodeError,
    /// the `result` range when the envelope read but `result` did not decode
    /// (`ClientDecodeError.raw`, PD-29)
    pub(crate) result: Option<Raw>,
    /// first occurrences counted before the failure: the counter already has them, so the
    /// caller logs them here or never
    pub(crate) first_seen: Vec<Seen>,
}

impl From<DecodeError> for BodyError {
    fn from(error: DecodeError) -> Self {
        Self {
            error,
            result: None,
            first_seen: Vec::new(),
        }
    }
}

/// What a response entry point returns.
pub(crate) type BodyResult<T> = Result<Decoded<Response<T>>, BodyError>;

/// One update with its own bytes. `Raw` offsets in `data` index `raw`.
#[derive(Debug)]
pub(crate) struct Item<T> {
    /// this update's bytes, copied out of the batch buffer (R04)
    pub(crate) raw: Arc<[u8]>,
    pub(crate) data: Result<T, UpdateError>,
}

/// An update that failed to decode (the Python class is B-05's `UpdateDecodeError`).
#[derive(Debug)]
pub(crate) struct UpdateError {
    /// read by a shallow scan, so it is there even when the rest is invalid; `None` when the
    /// key is absent or not an integer
    pub(crate) update_id: Option<i64>,
    pub(crate) error: DecodeError,
}

const OK: u16 = 0;
const RESULT: u16 = 1;
const ERROR_CODE: u16 = 2;
const DESCRIPTION: u16 = 3;

const fn f(wire: &'static str, kind: Kind) -> Field {
    Field {
        wire,
        kind,
        required: false,
        cold: false,
    }
}

static ENVELOPE: Table = Table {
    fields: &[
        f("ok", Kind::Bool),
        f("result", Kind::Opaque),
        f("error_code", Kind::I64),
        f("description", Kind::Str),
        f("parameters", Kind::Opaque),
    ],
    keys: &[
        ("description", DESCRIPTION),
        ("error_code", ERROR_CODE),
        ("ok", OK),
        ("parameters", 4),
        ("result", RESULT),
    ],
};

/// Decodes a method response in one pass: `result` is read in place by `read` where it stands
/// (no tree, no second pass; 13 B22). `read` is `Cursor::bool`, `Message::decode`,
/// `|c| c.opt(…)` for a nullable result, and so on.
pub(crate) fn decode_response<T>(
    body: &[u8],
    read: fn(&mut Cursor<'_>) -> DecodeResult<T>,
    options: Options,
) -> BodyResult<T> {
    respond(Cursor::new(body, 0)?, body, read, options)
}

fn respond<T>(
    c: Cursor<'_>,
    body: &[u8],
    read: fn(&mut Cursor<'_>) -> DecodeResult<T>,
    options: Options,
) -> BodyResult<T> {
    let mut c = c.strict(options.strict);
    let out = envelope(&mut c, body, read);
    let first_seen = c.take_seen();
    match out {
        Ok(value) => Ok(Decoded { value, first_seen }),
        Err(mut error) => {
            error.first_seen = first_seen;
            Err(error)
        }
    }
}

fn envelope<T>(
    c: &mut Cursor<'_>,
    body: &[u8],
    read: fn(&mut Cursor<'_>) -> DecodeResult<T>,
) -> Result<Response<T>, BodyError> {
    let mut ok = None;
    let mut result = None;
    let mut error_code = None;
    let mut description = None;
    let mut parameters = None;
    let mut present = [0u64; 1];
    let mut object = c.begin()?;
    while let Some(id) = c.field(&ENVELOPE, &mut object, &mut present)? {
        match id {
            OK => ok = c.opt(Cursor::bool)?,
            RESULT => {
                let start = c.mark();
                result = Some(match read(c) {
                    Ok(value) => Ok(value),
                    Err(error) => {
                        let error = error.at(Seg::Key("result"));
                        let Some(end) = scan::value_end(body, start as usize) else {
                            return Err(error.into());
                        };
                        let end = u32::try_from(end).unwrap_or(u32::MAX);
                        // go on after it: an `"ok":false` still makes this an `ApiError`
                        c.seek(end);
                        Err(BodyError {
                            result: Some(Raw { start, end }),
                            ..error.into()
                        })
                    }
                });
            }
            ERROR_CODE => error_code = c.opt(Cursor::i64)?,
            DESCRIPTION => description = c.opt(Cursor::str)?,
            _ => parameters = c.opt(Cursor::opaque)?,
        }
    }
    c.finish()?;
    match (ok, result) {
        (Some(true), Some(result)) => result.map(Response::Ok),
        (Some(true), None) => Err(DecodeError::missing("result", 0).into()),
        (Some(false), _) => Ok(Response::Err(ApiError {
            error_code,
            description,
            parameters,
        })),
        (None, _) => Err(DecodeError::missing("ok", 0).into()),
    }
}

/// Decodes a `getUpdates` response element by element (10 Layer 2): each update gets its own
/// copy of its bytes, and one that fails to decode is an [`UpdateError`] while the others are
/// unaffected. Only an element whose JSON does not even balance fails the body.
pub(crate) fn decode_updates<T: Decode>(
    body: &[u8],
    options: Options,
) -> BodyResult<Box<[Item<T>]>> {
    // a body that is not UTF-8 is checked element by element: one bad byte fails one update
    let c = match Cursor::new(body, 0) {
        Ok(c) => c,
        Err(_) => Cursor::unchecked(body, 0)?,
    };
    respond(c, body, items::<T>, options)
}

/// Decodes one update body (webhook, feed) with the same isolation as a `getUpdates` element.
pub(crate) fn decode_update<T: Decode>(raw: Arc<[u8]>, options: Options) -> Decoded<Item<T>> {
    let (data, first_seen) = match Cursor::new(&raw, 0) {
        Ok(c) => {
            let mut c = c.strict(options.strict);
            let data = T::decode(&mut c).and_then(|value| c.finish().map(|()| value));
            (data, c.take_seen())
        }
        Err(error) => (Err(error), Vec::new()),
    };
    let data = data.map_err(|error| UpdateError {
        update_id: scan::update_id(&raw),
        error,
    });
    Decoded {
        value: Item { raw, data },
        first_seen,
    }
}

/// The `result` array of `getUpdates`: one [`element`] per item.
fn items<T: Decode>(c: &mut Cursor<'_>) -> DecodeResult<Box<[Item<T>]>> {
    let mut out = Vec::new();
    let mut more = c.array()?;
    while more {
        let index = u32::try_from(out.len()).unwrap_or(u32::MAX);
        let start = c.mark();
        let mut e = c.element(start, None);
        let item = element::<T>(&mut e);
        c.extend_seen(e.take_seen());
        let (item, len) = item.map_err(|error| error.shifted(start).at(Seg::Index(index)))?;
        out.push(item);
        c.seek(start.saturating_add(len));
        more = c
            .array_next()
            .map_err(|error| error.at(Seg::Index(index)))?;
    }
    Ok(out.into_boxed_slice())
}

/// Decodes the update at the start of `e`'s input in one pass, then copies its bytes out
/// (R04): `e` starts its offsets at the element, so every `Raw` indexes the copy. Returns the
/// item and its length in the batch.
fn element<T: Decode>(e: &mut Cursor<'_>) -> DecodeResult<(Item<T>, u32)> {
    if e.is_utf8() {
        return decode_element(e);
    }
    // the body failed the UTF-8 check: check this update alone, within its own bounds
    let input = e.rest(0);
    let Some(len) = scan::value_end(input, 0) else {
        return Err(unbalanced(input));
    };
    let bytes = input.get(..len).unwrap_or_default();
    if let Err(error) = element_utf8(bytes) {
        let update_id = scan::update_id(bytes);
        let data = Err(UpdateError { update_id, error });
        let len = u32::try_from(len).unwrap_or(u32::MAX);
        return Ok((
            Item {
                raw: Arc::from(bytes),
                data,
            },
            len,
        ));
    }
    let mut checked = e.element(0, Some(len)).assume_utf8();
    let out = decode_element(&mut checked);
    e.extend_seen(checked.take_seen());
    out
}

/// The error for an element whose end cannot be found.
#[cold]
fn unbalanced(input: &[u8]) -> DecodeError {
    match Jiter::new(input).next_skip() {
        Err(error) => DecodeError::jiter(error, 0),
        Ok(()) => DecodeError::new(ErrorKind::Json("unbalanced brackets".into()), 0),
    }
}

/// [`element`] on a cursor whose input is UTF-8.
fn decode_element<T: Decode>(e: &mut Cursor<'_>) -> DecodeResult<(Item<T>, u32)> {
    let input = e.rest(0);
    let (data, len) = match T::decode(e) {
        Ok(value) => (Ok(value), e.mark() as usize),
        Err(error) => {
            // jiter cannot skip what it failed on (200 levels, a lone surrogate): the scanner can
            let Some(len) = scan::value_end(input, 0) else {
                return Err(error);
            };
            let update_id = input.get(..len).and_then(scan::update_id);
            (Err(UpdateError { update_id, error }), len)
        }
    };
    let raw: Arc<[u8]> = Arc::from(input.get(..len).unwrap_or_default());
    let len = u32::try_from(len).unwrap_or(u32::MAX);
    Ok((Item { raw, data }, len))
}
