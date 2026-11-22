//! The response envelope (05 §2.2, 13 B22) and per-update isolation (10 Layer 2, R04).
//!
//! Pure Rust: `&[u8]` in, owned values out, no Python objects. So the caller (B-05 / D-09) can
//! run each entry point inside `py.detach` (07 §2), and logs `first_seen` after it.

use std::sync::Arc;

use super::Decode;
use super::cursor::Cursor;
use super::error::{DecodeError, DecodeResult, Seg};
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
}

impl From<DecodeError> for BodyError {
    fn from(error: DecodeError) -> Self {
        Self {
            error,
            result: None,
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
    let mut c = Cursor::new(body, 0)?.strict(options.strict);
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
                match read(&mut c) {
                    Ok(value) => result = Some(value),
                    Err(error) => {
                        let local = start as usize;
                        let result = scan::value_end(body, local).map(|end| Raw {
                            start,
                            end: u32::try_from(end).unwrap_or(u32::MAX),
                        });
                        return Err(BodyError {
                            error: error.at(Seg::Key("result")),
                            result,
                        });
                    }
                }
            }
            ERROR_CODE => error_code = c.opt(Cursor::i64)?,
            DESCRIPTION => description = c.opt(Cursor::str)?,
            _ => parameters = c.opt(Cursor::opaque)?,
        }
    }
    c.finish()?;
    let value = match (ok, result) {
        (Some(true), Some(result)) => Response::Ok(result),
        (Some(true), None) => return Err(DecodeError::missing("result", 0).into()),
        (Some(false), _) => Response::Err(ApiError {
            error_code,
            description,
            parameters,
        }),
        (None, _) => return Err(DecodeError::missing("ok", 0).into()),
    };
    Ok(Decoded {
        value,
        first_seen: c.take_seen(),
    })
}

/// Decodes a `getUpdates` response element by element (10 Layer 2): each update gets its own
/// copy of its bytes, and one that fails to decode is an [`UpdateError`] while the others are
/// unaffected. Only an element whose JSON does not even balance fails the body.
pub(crate) fn decode_updates<T: Decode>(
    body: &[u8],
    options: Options,
) -> BodyResult<Box<[Item<T>]>> {
    decode_response(body, items::<T>, options)
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
        let mut e = c.element(start);
        let (item, len) = element::<T>(&mut e).map_err(|error| error.at(Seg::Index(index)))?;
        c.extend_seen(e.take_seen());
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
