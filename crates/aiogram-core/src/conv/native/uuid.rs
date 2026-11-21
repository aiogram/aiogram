//! UUID text: `8-4-4-4-12` hex (canonical) or 32 hex digits.

const HEX: &[u8; 16] = b"0123456789abcdef";

/// Byte offsets of the hyphens in the canonical form.
const HYPHENS: [usize; 4] = [8, 13, 18, 23];

/// The 128-bit value of a canonical (`12345678-1234-...`) or 32-digit hex UUID, any case.
/// `None` for anything else (the caller falls back to `uuid.UUID(text)` for the rarer forms:
/// braces, `urn:uuid:`, other hyphen placements).
pub(crate) fn parse(text: &str) -> Option<u128> {
    let bytes = text.as_bytes();
    let canonical = match bytes.len() {
        32 => false,
        36 => true,
        _ => return None,
    };
    let mut value: u128 = 0;
    for (i, &b) in bytes.iter().enumerate() {
        if canonical && HYPHENS.contains(&i) {
            if b != b'-' {
                return None;
            }
            continue;
        }
        // per byte: a non-ASCII byte is never a hex digit
        let digit = char::from(b).to_digit(16)?;
        value = (value << 4) | u128::from(digit);
    }
    Some(value)
}

/// Append the canonical lower-case text, or 32 lower-case hex digits with `hex`.
pub(crate) fn write(value: u128, hex: bool, out: &mut String) {
    out.reserve(if hex { 32 } else { 36 });
    for i in 0..32 {
        if !hex && matches!(i, 8 | 12 | 16 | 20) {
            out.push('-');
        }
        let nibble = (value >> (124 - 4 * i)) & 0xf;
        out.push(char::from(HEX[nibble as usize]));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // uuid.UUID('12345678-1234-5678-9abc-def012345678').int
    const VALUE: u128 = 24197857161011715172010103071957079672;

    #[test]
    fn parses_canonical_and_hex_any_case() {
        assert_eq!(parse("12345678-1234-5678-9abc-def012345678"), Some(VALUE));
        assert_eq!(parse("12345678-1234-5678-9ABC-DEF012345678"), Some(VALUE));
        assert_eq!(parse("12345678123456789abcdef012345678"), Some(VALUE));
        assert_eq!(parse("12345678123456789AbCdEf012345678"), Some(VALUE));
        assert_eq!(parse("00000000-0000-0000-0000-000000000000"), Some(0));
        assert_eq!(
            parse("ffffffff-ffff-ffff-ffff-ffffffffffff"),
            Some(u128::MAX)
        );
    }

    #[test]
    fn defers_other_forms() {
        for text in [
            "",
            "{12345678-1234-5678-9abc-def012345678}",
            "urn:uuid:12345678-1234-5678-9abc-def012345678",
            "12345678_1234_5678_9abc_def012345678",
            "12345678-1234-5678-9abc-def01234567g",
            "12345678123456789abcdef01234567",
            "12345678123456789abcdef0123456789",
            "+2345678123456789abcdef012345678",
            // 36 bytes, a hyphen moved
            "123456781-234-5678-9abc-def012345678",
            // 32 hex digits with hyphens in the wrong places
            "1234567812345678-9abc-def012345678",
            // a non-ASCII digit
            "١2345678123456789abcdef01234567",
        ] {
            assert_eq!(parse(text), None, "{text:?}");
        }
    }

    #[test]
    fn writes_lower_case() {
        let mut out = String::new();
        write(VALUE, false, &mut out);
        assert_eq!(out, "12345678-1234-5678-9abc-def012345678");
        out.clear();
        write(VALUE, true, &mut out);
        assert_eq!(out, "12345678123456789abcdef012345678");
        out.clear();
        write(1, false, &mut out);
        assert_eq!(out, "00000000-0000-0000-0000-000000000001");
    }

    #[test]
    fn round_trips() {
        let mut x: u128 = 0x9e37_79b9_7f4a_7c15_f39c_c060_5ced_c834;
        for _ in 0..1000 {
            x = x
                .wrapping_mul(0x2545_f491_4f6c_dd1d)
                .wrapping_add(0x1405_7b7e_f767_814f)
                ^ (x >> 67);
            let mut out = String::new();
            write(x, false, &mut out);
            assert_eq!(parse(&out), Some(x));
            out.clear();
            write(x, true, &mut out);
            assert_eq!(parse(&out), Some(x));
        }
    }
}
