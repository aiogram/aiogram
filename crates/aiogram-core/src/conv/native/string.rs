//! JSON string escaping as `json.dumps(ensure_ascii=False)` writes it.
//!
//! Only `"`, `\` and the C0 controls are escaped (`\n`, `\r`, `\t`, `\b`, `\f`, the rest as
//! `\u00XX` with lower-case hex); everything else, U+007F and U+2028/U+2029 included, is copied
//! as raw UTF-8.

const HEX: &[u8; 16] = b"0123456789abcdef";

/// Append `text` as a quoted JSON string.
pub(crate) fn write_str(text: &str, out: &mut Vec<u8>) {
    let bytes = text.as_bytes();
    out.reserve(bytes.len() + 2);
    out.push(b'"');
    // copy runs of bytes that need no escape in one go; every escaped byte is ASCII, so a
    // multi-byte character is never split
    let mut run = 0;
    for (i, &b) in bytes.iter().enumerate() {
        let escape: &[u8] = match b {
            b'"' => b"\\\"",
            b'\\' => b"\\\\",
            b'\n' => b"\\n",
            b'\r' => b"\\r",
            b'\t' => b"\\t",
            0x08 => b"\\b",
            0x0c => b"\\f",
            0x00..=0x1f => &[
                b'\\',
                b'u',
                b'0',
                b'0',
                HEX[usize::from(b >> 4)],
                HEX[usize::from(b & 0xf)],
            ],
            _ => continue,
        };
        out.extend_from_slice(&bytes[run..i]);
        out.extend_from_slice(escape);
        run = i + 1;
    }
    out.extend_from_slice(&bytes[run..]);
    out.push(b'"');
}

#[cfg(test)]
mod tests {
    use super::*;

    fn json(text: &str) -> Vec<u8> {
        let mut out = Vec::new();
        write_str(text, &mut out);
        out
    }

    #[test]
    fn escapes_like_json_dumps() {
        // json.dumps(''.join(map(chr, range(0x30))) + '\x7f\u2028\u2029\ud7ff\ue000\U0001F600é"\\',
        //            ensure_ascii=False).encode()
        let text: String = (0..0x30u8).map(char::from).collect::<String>()
            + "\u{7f}\u{2028}\u{2029}\u{d7ff}\u{e000}\u{1F600}é\"\\";
        let expected: &[u8] = b"\"\\u0000\\u0001\\u0002\\u0003\\u0004\\u0005\\u0006\\u0007\\b\\t\\n\\u000b\\f\\r\\u000e\\u000f\\u0010\\u0011\\u0012\\u0013\\u0014\\u0015\\u0016\\u0017\\u0018\\u0019\\u001a\\u001b\\u001c\\u001d\\u001e\\u001f !\\\"#$%&'()*+,-./\x7f\xe2\x80\xa8\xe2\x80\xa9\xed\x9f\xbf\xee\x80\x80\xf0\x9f\x98\x80\xc3\xa9\\\"\\\\\"";
        assert_eq!(json(&text), expected);
    }

    #[test]
    fn copies_plain_text() {
        assert_eq!(json(""), b"\"\"");
        assert_eq!(json("hello, мир"), "\"hello, мир\"".as_bytes());
        assert_eq!(json("a\"b"), b"\"a\\\"b\"");
        assert_eq!(json("\n"), b"\"\\n\"");
    }

    #[test]
    fn appends() {
        let mut out = b"[".to_vec();
        write_str("x", &mut out);
        assert_eq!(out, b"[\"x\"");
    }
}
