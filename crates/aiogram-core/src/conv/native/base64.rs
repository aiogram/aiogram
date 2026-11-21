//! Base64: padded standard alphabet (JSON) and unpadded url-safe alphabet (flat form).
//!
//! Decoding is strict: no whitespace, no character outside the alphabet. Like CPython's
//! `binascii`, it ignores the unused low bits of the last character (`QR==` decodes to `A` as
//! `QQ==` does), so `encode(decode(text))` may differ from `text`.

const STANDARD: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
const URL_SAFE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

/// Encode `data`: padded standard base64, or unpadded base64url with `url`.
pub(crate) fn encode(data: &[u8], url: bool) -> String {
    let alphabet = if url { URL_SAFE } else { STANDARD };
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let b = [
            chunk[0],
            *chunk.get(1).unwrap_or(&0),
            *chunk.get(2).unwrap_or(&0),
        ];
        let n = (u32::from(b[0]) << 16) | (u32::from(b[1]) << 8) | u32::from(b[2]);
        let chars = [(n >> 18) & 63, (n >> 12) & 63, (n >> 6) & 63, n & 63];
        for (i, c) in chars.iter().enumerate() {
            if i <= chunk.len() {
                out.push(char::from(alphabet[*c as usize]));
            } else if !url {
                out.push('=');
            }
        }
    }
    out
}

/// Decode strictly; `None` when `text` is not valid.
///
/// - standard (`url` false): what `base64.b64decode(text, validate=True)` accepts: a multiple of
///   4 characters, `=` only as one or two final pad characters;
/// - url-safe (`url` true): the url-safe alphabet with no padding at all, so any length but
///   `4n + 1` (what `urlsafe_b64decode` accepts once the padding is added back).
pub(crate) fn decode(text: &str, url: bool) -> Option<Vec<u8>> {
    let mut body = text.as_bytes();
    if !url {
        if !body.len().is_multiple_of(4) {
            return None;
        }
        body = body
            .strip_suffix(b"==")
            .or_else(|| body.strip_suffix(b"="))
            .unwrap_or(body);
    }
    if body.len() % 4 == 1 {
        return None;
    }
    let mut out = Vec::with_capacity(body.len() * 3 / 4);
    for chunk in body.chunks(4) {
        let mut n: u32 = 0;
        for &c in chunk {
            n = (n << 6) | u32::from(value(c, url)?);
        }
        // left-align a short final chunk, then keep its whole bytes: 2 chars -> 1, 3 -> 2
        n <<= 6 * (4 - chunk.len() as u32);
        out.extend_from_slice(&n.to_be_bytes()[1..chunk.len()]);
    }
    Some(out)
}

/// The 6-bit value of an alphabet character; `None` for anything else (`=` included).
fn value(c: u8, url: bool) -> Option<u8> {
    Some(match c {
        b'A'..=b'Z' => c - b'A',
        b'a'..=b'z' => c - b'a' + 26,
        b'0'..=b'9' => c - b'0' + 52,
        b'+' if !url => 62,
        b'/' if !url => 63,
        b'-' if url => 62,
        b'_' if url => 63,
        _ => return None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    // CPython 3.11 / 3.14: `base64.b64decode(text, validate=True)`, `None` for binascii.Error
    const STANDARD_DECODES: &[(&str, Option<&[u8]>)] = &[
        ("", Some(b"")),
        ("QQ==", Some(b"A")),
        ("QR==", Some(b"A")),
        ("QUE=", Some(b"AA")),
        ("QUF=", Some(b"AA")),
        ("QUFB", Some(b"AAA")),
        ("Q+/A", Some(b"C\xef\xc0")),
        ("QQ", None),
        ("QQ=", None),
        ("Q===", None),
        ("====", None),
        ("QQ==QQ==", None),
        ("QU=E", None),
        ("Q", None),
        ("QUFBQ", None),
        ("QQ== ", None),
        (" QQ==", None),
        ("QQ\n==", None),
        ("Q-_=", None),
        ("=QQ=", None),
        ("QQ=A", None),
    ];

    // CPython: `urlsafe_b64decode(text + "=" * (-len(text) % 4))` for url-safe-alphabet text
    const URL_DECODES: &[(&str, Option<&[u8]>)] = &[
        ("", Some(b"")),
        ("QQ", Some(b"A")),
        ("QR", Some(b"A")),
        ("QUE", Some(b"AA")),
        ("QUF", Some(b"AA")),
        ("QUFB", Some(b"AAA")),
        ("-_8", Some(b"\xfb\xff")),
        ("Q", None),
        ("QUFBQ", None),
        ("+/8", None),
        ("QQ==", None),
        ("QQ=", None),
        ("QQ ", None),
    ];

    // CPython: `b64encode(data)`, `urlsafe_b64encode(data).rstrip(b"=")`
    const ENCODES: &[(&[u8], &str, &str)] = &[
        (b"", "", ""),
        (b"f", "Zg==", "Zg"),
        (b"fo", "Zm8=", "Zm8"),
        (b"foo", "Zm9v", "Zm9v"),
        (b"foob", "Zm9vYg==", "Zm9vYg"),
        (b"\xfb\xff\xfe", "+//+", "-__-"),
        (
            b"\x00\x10\x83\x10Q\x87 \x92\x8b0\xd3\x8fA\x14\x93",
            "ABCDEFGHIJKLMNOPQRST",
            "ABCDEFGHIJKLMNOPQRST",
        ),
    ];

    #[test]
    fn decodes_like_cpython() {
        for (text, expected) in STANDARD_DECODES {
            assert_eq!(decode(text, false).as_deref(), *expected, "{text:?}");
        }
        for (text, expected) in URL_DECODES {
            assert_eq!(decode(text, true).as_deref(), *expected, "{text:?}");
        }
    }

    #[test]
    fn encodes_like_cpython() {
        for (data, standard, url) in ENCODES {
            assert_eq!(encode(data, false), *standard);
            assert_eq!(encode(data, true), *url);
        }
    }

    #[test]
    fn round_trips_every_length_and_byte() {
        let data: Vec<u8> = (0..=255u8).chain((0..=255u8).rev()).collect();
        for len in 0..data.len() {
            let data = &data[..len];
            for url in [false, true] {
                assert_eq!(
                    decode(&encode(data, url), url).as_deref(),
                    Some(data),
                    "{len} {url}"
                );
            }
        }
    }
}
