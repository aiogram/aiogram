//! A structural scanner for the failure paths. It finds where a JSON value ends, and reads a
//! top-level key of an object, by structure only: strings with their `\` escapes and the
//! bracket balance. Nothing else is validated, and nesting is unlimited (it is iterative).
//!
//! jiter can't do this here. `known_skip` stops at 200 nested levels and rejects a lone
//! surrogate escape. Without this scanner, an update that failed for either reason would leave
//! the `getUpdates` batch with no end for that element, and the whole batch would fail (10 §1).

use jiter::{Jiter, NumberInt};

fn ws(buf: &[u8], mut i: usize) -> usize {
    while buf.get(i).is_some_and(u8::is_ascii_whitespace) {
        i += 1;
    }
    i
}

/// The index past the closing quote of the string whose opening quote is at `i`.
fn string_end(buf: &[u8], i: usize) -> Option<usize> {
    let mut j = i.checked_add(1)?;
    loop {
        match *buf.get(j)? {
            b'"' => return j.checked_add(1),
            b'\\' => j = j.checked_add(2)?,
            _ => j += 1,
        }
    }
}

/// The end (exclusive) of the value that starts at `start`, after any whitespace; `None` if the
/// input ends first or the brackets do not balance (a `}` closing a `[` included, so a broken
/// element never swallows the ones after it).
pub(crate) fn value_end(buf: &[u8], start: usize) -> Option<usize> {
    let mut i = ws(buf, start);
    // the closer each open bracket expects; memory grows with the nesting, the stack does not
    let mut open: Vec<u8> = Vec::new();
    loop {
        match *buf.get(i)? {
            b'"' => {
                i = string_end(buf, i)?;
                if open.is_empty() {
                    return Some(i);
                }
                continue;
            }
            b'{' => open.push(b'}'),
            b'[' => open.push(b']'),
            close @ (b'}' | b']') => {
                if open.pop()? != close {
                    return None;
                }
                if open.is_empty() {
                    return i.checked_add(1);
                }
            }
            _ if open.is_empty() => {
                // a scalar: up to the next delimiter
                let len = buf
                    .get(i..)?
                    .iter()
                    .position(|b| matches!(b, b',' | b'}' | b']') || b.is_ascii_whitespace())
                    .unwrap_or(buf.len() - i);
                return (len > 0).then_some(i + len);
            }
            _ => {}
        }
        i += 1;
    }
}

/// The integer at top-level key `update_id` of the object `buf` holds; `None` if it is absent or
/// not an integer. The last occurrence wins, as in decoding; a scan that breaks off keeps what it
/// found so far. The other values are only skipped, so an update that fails to decode still gives
/// its id (10 Layer 2).
pub(crate) fn update_id(buf: &[u8]) -> Option<i64> {
    let mut found = None;
    scan_update_id(buf, &mut found);
    found.flatten()
}

/// Sets `found` at each `update_id` key: `Some(None)` for a value that is not an integer.
fn scan_update_id(buf: &[u8], found: &mut Option<Option<i64>>) -> Option<()> {
    let mut i = ws(buf, 0);
    if buf.get(i) != Some(&b'{') {
        return None;
    }
    i = ws(buf, i + 1);
    loop {
        if buf.get(i) != Some(&b'"') {
            return None;
        }
        let key_end = string_end(buf, i)?;
        let key = buf.get(i + 1..key_end - 1)?;
        i = ws(buf, key_end);
        if buf.get(i) != Some(&b':') {
            return None;
        }
        let value = ws(buf, i + 1);
        let end = value_end(buf, value)?;
        if key == b"update_id" {
            *found = Some(match Jiter::new(buf.get(value..end)?).next_int() {
                Ok(NumberInt::Int(id)) => Some(id),
                _ => None,
            });
        }
        i = ws(buf, end);
        if buf.get(i) != Some(&b',') {
            return None;
        }
        i = ws(buf, i + 1);
    }
}
