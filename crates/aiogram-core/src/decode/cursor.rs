//! The class-independent half of the decoder (13 B21): one jiter pass, key lookup, unknown-key
//! ranges, present bits and the value readers. Nothing here is generic over the decoded type
//! except the `fn`-pointer helpers `opt` and `list`, one instance per value type.

use jiter::{Jiter, NumberInt, Peek};

use super::error::{DecodeError, DecodeResult, ErrorKind, Seg};
use super::table::Table;
use super::value::{IStr, Meta, Raw, UnixTime, Unknown, set_bit};

/// A pull decoder over one buffer: the update's own bytes, or a sub-slice of them at `base`
/// (B-14 decodes a union member on a fresh cursor over its slice). Every recorded [`Raw`] is
/// an offset into the update's buffer.
pub(crate) struct Cursor<'j> {
    /// the whole input, at `origin_base`
    origin: &'j [u8],
    origin_base: u32,
    /// the part `jiter` reads: `origin` from `base` on (moved by [`recover`](Self::recover))
    data: &'j [u8],
    jiter: Jiter<'j>,
    base: u32,
}

/// An object being decoded: built by [`Cursor::begin`], fed by [`Cursor::field`].
pub(crate) struct Object {
    start: u32,
    end: u32,
    first: bool,
    unknown: Vec<Unknown>,
    /// fields whose last occurrence so far failed; empty unless the input is invalid
    failed: Vec<(u16, DecodeError)>,
}

impl Object {
    /// Field `id` was read: an earlier failed occurrence of it is overwritten (last wins).
    #[inline]
    pub(crate) fn settled(&mut self, id: u16) {
        if !self.failed.is_empty() {
            self.failed.retain(|(failed, _)| *failed != id);
        }
    }

    /// The header of the finished object, or the first error that no later duplicate overwrote.
    pub(crate) fn meta<B>(self, present: B) -> DecodeResult<Meta<B>> {
        if let Some((_, error)) = self.failed.into_iter().next() {
            return Err(error);
        }
        Ok(Meta {
            span: Raw {
                start: self.start,
                end: self.end,
            },
            present,
            unknown: self.unknown.into_boxed_slice(),
        })
    }
}

impl<'j> Cursor<'j> {
    /// A cursor over `data`, which starts at byte `base` of the update's buffer. The whole of
    /// `data` must be UTF-8: jiter does not check it in keys and skipped values.
    pub(crate) fn new(data: &'j [u8], base: u32) -> DecodeResult<Self> {
        if u32::try_from(data.len())
            .ok()
            .and_then(|len| len.checked_add(base))
            .is_none()
        {
            return Err(DecodeError::new(ErrorKind::TooLarge, base));
        }
        if let Err(e) = std::str::from_utf8(data) {
            let at = u32::try_from(e.valid_up_to()).unwrap_or(u32::MAX);
            return Err(DecodeError::new(
                ErrorKind::Json("invalid UTF-8".into()),
                base.saturating_add(at),
            ));
        }
        Ok(Self {
            origin: data,
            origin_base: base,
            data,
            jiter: Jiter::new(data),
            base,
        })
    }

    /// Where the next value starts, for [`recover`](Self::recover).
    pub(crate) fn mark(&self) -> u32 {
        self.here()
    }

    /// After reading field `id` (its value at `mark`) failed with `error`: skips that value on a
    /// fresh jiter and goes on after it, so the rest of the object is read and a later duplicate
    /// can still win. Invalid JSON in the value is the error.
    #[cold]
    pub(crate) fn recover(
        &mut self,
        table: &Table,
        object: &mut Object,
        mark: u32,
        id: u16,
        error: DecodeError,
    ) -> DecodeResult<()> {
        let at = Seg::Key(table.wire(id));
        let local = mark.saturating_sub(self.origin_base) as usize;
        let mut jiter = Jiter::new(self.origin.get(local..).unwrap_or_default());
        if let Err(skip) = jiter.next_skip() {
            // invalid JSON wins; a nested level already reported it with the finer path
            return Err(if matches!(error.kind(), ErrorKind::Json(_)) {
                error.at(at)
            } else {
                DecodeError::jiter(skip, mark).at(at)
            });
        }
        let end = local.saturating_add(jiter.current_index());
        self.data = self.origin.get(end..).unwrap_or_default();
        self.base = self
            .origin_base
            .saturating_add(u32::try_from(end).unwrap_or(u32::MAX));
        self.jiter = Jiter::new(self.data);
        object.failed.push((id, error.at(at)));
        Ok(())
    }

    /// Offset in the update's buffer of `index` in `data`. Exact: `new` keeps `base + len`
    /// within `u32`, and every index is at most `len`.
    fn pos(&self, index: usize) -> u32 {
        self.base
            .saturating_add(u32::try_from(index).unwrap_or(u32::MAX))
    }

    fn here(&self) -> u32 {
        self.pos(self.jiter.current_index())
    }

    fn fail(&self, error: jiter::JiterError) -> DecodeError {
        DecodeError::jiter(error, self.base)
    }

    fn peek(&mut self) -> DecodeResult<Peek> {
        self.jiter.peek().map_err(|e| self.fail(e))
    }

    /// Nothing but whitespace is left.
    pub(crate) fn finish(&mut self) -> DecodeResult<()> {
        self.jiter.finish().map_err(|e| self.fail(e))
    }

    /// Starts an object; the `{` itself is checked by the first [`field`](Self::field) call.
    pub(crate) fn begin(&mut self) -> DecodeResult<Object> {
        self.peek()?;
        Ok(Object {
            start: self.here(),
            end: 0,
            first: true,
            unknown: Vec::new(),
            failed: Vec::new(),
        })
    }

    /// The id of the next known field of `object`, with its present bit set; `None` at `}`.
    /// Unknown keys on the way are recorded as raw ranges and skipped: their values are checked
    /// as JSON syntax only, escapes included (a lone surrogate in one is an error here too).
    pub(crate) fn field(
        &mut self,
        table: &Table,
        object: &mut Object,
        present: &mut [u64],
    ) -> DecodeResult<Option<u16>> {
        loop {
            let step = if object.first {
                object.first = false;
                self.jiter.next_object_bytes()
            } else {
                self.jiter.next_key_bytes()
            };
            // jiter hands out the key's bytes inside `data`, escapes not decoded
            let (start, end) = match step {
                Ok(Some(key)) => {
                    let start = key.as_ptr().addr().wrapping_sub(self.data.as_ptr().addr());
                    (start, start.wrapping_add(key.len()))
                }
                Ok(None) => {
                    object.end = self.here();
                    return Ok(None);
                }
                Err(e) => return Err(self.fail(e)),
            };
            let key = self.data.get(start..end).unwrap_or_default();
            let id = if key.contains(&b'\\') {
                self.escaped_key(table, start, end)?
            } else {
                table.lookup(key)
            };
            if let Some(id) = id {
                set_bit(present, id);
                return Ok(Some(id));
            }
            let value = self.opaque()?;
            object.unknown.push(Unknown {
                key: Raw {
                    start: self.pos(start),
                    end: self.pos(end),
                },
                value,
            });
        }
    }

    /// A key with escapes: decoded, then looked up. Telegram never sends one.
    #[cold]
    fn escaped_key(&self, table: &Table, start: usize, end: usize) -> DecodeResult<Option<u16>> {
        // the quotes around the key are part of `data`
        let quoted = self
            .data
            .get(start.saturating_sub(1)..end.saturating_add(1))
            .unwrap_or_default();
        let base = self.pos(start.saturating_sub(1));
        let mut jiter = Jiter::new(quoted);
        match jiter.next_str() {
            Ok(key) => Ok(table.lookup(key.as_bytes())),
            Err(e) => Err(DecodeError::jiter(e, base)),
        }
    }

    /// `null` is `None`, anything else is `read`. The field readers of a type's `set`.
    pub(crate) fn opt<T>(
        &mut self,
        read: fn(&mut Self) -> DecodeResult<T>,
    ) -> DecodeResult<Option<T>> {
        if self.peek()? == Peek::Null {
            self.jiter.known_null().map_err(|e| self.fail(e))?;
            return Ok(None);
        }
        read(self).map(Some)
    }

    /// A JSON array of `item`s; an error carries the item's index.
    pub(crate) fn list<T>(
        &mut self,
        item: fn(&mut Self) -> DecodeResult<T>,
    ) -> DecodeResult<Box<[T]>> {
        let mut out = Vec::new();
        let mut next = self.jiter.next_array().map_err(|e| self.fail(e))?;
        while next.is_some() {
            let index = u32::try_from(out.len()).unwrap_or(u32::MAX);
            out.push(item(self).map_err(|e| e.at(Seg::Index(index)))?);
            next = self
                .jiter
                .array_step()
                .map_err(|e| self.fail(e).at(Seg::Index(index)))?;
        }
        Ok(out.into_boxed_slice())
    }

    pub(crate) fn bool(&mut self) -> DecodeResult<bool> {
        self.jiter.next_bool().map_err(|e| self.fail(e))
    }

    pub(crate) fn i64(&mut self) -> DecodeResult<i64> {
        self.peek()?;
        let at = self.here();
        match self.jiter.next_int() {
            Ok(NumberInt::Int(value)) => Ok(value),
            Ok(NumberInt::BigInt(_)) => Err(DecodeError::new(ErrorKind::Range("i64"), at)),
            Err(e) => Err(self.fail(e)),
        }
    }

    pub(crate) fn i32(&mut self) -> DecodeResult<i32> {
        self.peek()?;
        let at = self.here();
        let range = || DecodeError::new(ErrorKind::Range("i32"), at);
        match self.i64() {
            Ok(value) => i32::try_from(value).map_err(|_| range()),
            Err(e) if matches!(e.kind(), ErrorKind::Range(_)) => Err(range()),
            Err(e) => Err(e),
        }
    }

    /// A JSON number; an integer literal is accepted.
    pub(crate) fn f64(&mut self) -> DecodeResult<f64> {
        self.jiter.next_float().map_err(|e| self.fail(e))
    }

    pub(crate) fn str(&mut self) -> DecodeResult<Box<str>> {
        match self.jiter.next_str() {
            Ok(value) => Ok(value.into()),
            Err(e) => Err(self.fail(e)),
        }
    }

    pub(crate) fn istr(&mut self) -> DecodeResult<IStr> {
        match self.jiter.next_str() {
            Ok(value) => Ok(IStr::new(value)),
            Err(e) => Err(self.fail(e)),
        }
    }

    pub(crate) fn time(&mut self) -> DecodeResult<UnixTime> {
        self.i64().map(UnixTime)
    }

    /// The next value as a raw range, checked as JSON syntax only (out-of-set fields, B-04).
    pub(crate) fn opaque(&mut self) -> DecodeResult<Raw> {
        let peek = self.peek()?;
        let start = self.here();
        self.jiter.known_skip(peek).map_err(|e| self.fail(e))?;
        Ok(Raw {
            start,
            end: self.here(),
        })
    }

    /// A wire enum value: the index into `names` (sorted), or the unknown string itself.
    pub(crate) fn choice(&mut self, names: &[&str]) -> DecodeResult<Result<usize, Box<str>>> {
        match self.jiter.next_str() {
            Ok(value) => Ok(names
                .binary_search_by(|name| (*name).cmp(value))
                .map_err(|_| value.into())),
            Err(e) => Err(self.fail(e)),
        }
    }
}
