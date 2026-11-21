//! JSON numbers as Python writes floats: `repr(float)` (shortest round-trip text, exponent form
//! below 1e-4 and from 1e16), and `NaN` / `Infinity` / `-Infinity` as `json.dumps` writes them.

use std::io::Write;

/// Append `value` as `json.dumps` would write it.
pub(crate) fn write_float(value: f64, out: &mut Vec<u8>) {
    if value.is_nan() {
        out.extend_from_slice(b"NaN");
        return;
    }
    if value.is_infinite() {
        out.extend_from_slice(if value > 0.0 {
            b"Infinity"
        } else {
            b"-Infinity"
        });
        return;
    }
    // `{:e}` gives the shortest round-trip digits, as `repr` picks them: `-1.2345e-5`, `1e16`,
    // `0e0`; write it at the end of `out`, take the digits and the exponent, and lay them out
    // again the way `repr` does
    let start = out.len();
    // writing into a `Vec` cannot fail
    let _ = write!(out, "{value:e}");
    let mut digits = [0u8; 17];
    let mut count = 0;
    let mut exponent: i32 = 0;
    let mut exponent_negative = false;
    let mut in_exponent = false;
    for &b in &out[start..] {
        match b {
            b'e' => in_exponent = true,
            b'-' if in_exponent => exponent_negative = true,
            b'0'..=b'9' if in_exponent => exponent = exponent * 10 + i32::from(b - b'0'),
            b'0'..=b'9' if count < digits.len() => {
                digits[count] = b;
                count += 1;
            }
            _ => {}
        }
    }
    if exponent_negative {
        exponent = -exponent;
    }
    out.truncate(start);
    let digits = &mut digits[..count];
    round_tie_to_even(value, digits, exponent);
    let digits = &*digits;
    if value.is_sign_negative() {
        out.push(b'-');
    }

    if !(-4..16).contains(&exponent) {
        // `d[.ddd]e±XX`: no `.0`, the exponent signed and at least two digits
        out.push(digits[0]);
        if digits.len() > 1 {
            out.push(b'.');
            out.extend_from_slice(&digits[1..]);
        }
        out.push(b'e');
        out.push(if exponent < 0 { b'-' } else { b'+' });
        let exponent = exponent.unsigned_abs();
        if exponent < 10 {
            out.push(b'0');
        }
        let _ = write!(out, "{exponent}");
    } else if exponent >= 0 {
        // `ddd.ddd`, zeros to the decimal point and `.0` for an integral value
        let point = exponent as usize + 1;
        if digits.len() > point {
            out.extend_from_slice(&digits[..point]);
            out.push(b'.');
            out.extend_from_slice(&digits[point..]);
        } else {
            out.extend_from_slice(digits);
            out.resize(out.len() + point - digits.len(), b'0');
            out.extend_from_slice(b".0");
        }
    } else {
        // `0.000ddd`
        out.extend_from_slice(b"0.");
        out.resize(out.len() + (-exponent - 1) as usize, b'0');
        out.extend_from_slice(digits);
    }
}

/// Fix the one case where `{:e}` and `repr` pick different shortest digits.
///
/// When the exact value lies halfway between two shortest candidates (`2247721593076182.25`
/// between `…182.2` and `…182.3`), Rust rounds the tie up and CPython (David Gay's `dtoa`) to
/// the even digit. So when the digits end odd, the value is exactly the midpoint below them and
/// the lower candidate still reads back as `value`, take the lower one.
fn round_tie_to_even(value: f64, digits: &mut [u8], exponent: i32) {
    let count = digits.len();
    let last = digits[count - 1];
    if (last - b'0').is_multiple_of(2) {
        return;
    }
    // the midpoint: the lower candidate and a `5`, `count + 1` digits times 10^(exponent - count)
    let midpoint = digits
        .iter()
        .fold(0u64, |n, &d| n * 10 + u64::from(d - b'0'))
        * 10
        - 5;
    let (mantissa, binary_exponent) = decompose(value);
    if !exactly_equal(mantissa, binary_exponent, midpoint, exponent - count as i32) {
        return;
    }
    // check the round trip: below a power of two the lower side of the rounding interval is
    // narrower, so the lower candidate may read back as the next float down
    let mut candidate = [0u8; 32];
    candidate[..count].copy_from_slice(digits);
    candidate[count - 1] = last - 1;
    let mut tail = &mut candidate[count..];
    // `ddde-x`: at most 17 + 5 bytes, so it fits
    let _ = write!(tail, "e{}", exponent - count as i32 + 1);
    let len = 32 - tail.len();
    let reads_back = std::str::from_utf8(&candidate[..len])
        .ok()
        .and_then(|text| text.parse::<f64>().ok())
        .is_some_and(|parsed| parsed == value.abs());
    // never a trailing `0`: a shorter text would read back, and `{:e}` would have found it
    if reads_back {
        digits[count - 1] = last - 1;
    }
}

/// `value.abs()` as `mantissa * 2^exponent`; `value` is finite and not zero.
fn decompose(value: f64) -> (u64, i32) {
    let bits = value.to_bits();
    let fraction = bits & ((1 << 52) - 1);
    let biased = ((bits >> 52) & 0x7ff) as i32;
    if biased == 0 {
        (fraction, -1074)
    } else {
        (fraction | (1 << 52), biased - 1075)
    }
}

/// Whether `m * 2^e == d * 10^q`, for non-zero `m` and `d`: two rationals are equal when their
/// powers of 2 and of 5 agree and what is left of the integers is the same.
fn exactly_equal(m: u64, e: i32, d: u64, q: i32) -> bool {
    let (m2, m) = strip(m, 2);
    let (m5, m) = strip(m, 5);
    let (d2, d) = strip(d, 2);
    let (d5, d) = strip(d, 5);
    m == d && m2 + e == d2 + q && m5 == d5 + q
}

/// `n` without its factors `p`, and how many there were.
fn strip(mut n: u64, p: u64) -> (i32, u64) {
    let mut count = 0;
    while n.is_multiple_of(p) {
        n /= p;
        count += 1;
    }
    (count, n)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn text(value: f64) -> String {
        let mut out = Vec::new();
        write_float(value, &mut out);
        String::from_utf8(out).unwrap()
    }

    // CPython `repr(value)`; the ties are written as their exact values
    #[allow(clippy::excessive_precision)]
    const EDGES: &[(f64, &str)] = &[
        (0.0, "0.0"),
        (-0.0, "-0.0"),
        (1.0, "1.0"),
        (-1.5, "-1.5"),
        (0.1, "0.1"),
        (0.0001, "0.0001"),
        (0.00001, "1e-05"),
        (1.5e-05, "1.5e-05"),
        (1.23e-05, "1.23e-05"),
        (0.001, "0.001"),
        (12345.678, "12345.678"),
        (100.0, "100.0"),
        (0.30000000000000004, "0.30000000000000004"),
        (123456789012345.6, "123456789012345.6"),
        (1e15, "1000000000000000.0"),
        (9999999999999998.0, "9999999999999998.0"),
        (9007199254740992.0, "9007199254740992.0"),
        (1e16, "1e+16"),
        (1.2345e16, "1.2345e+16"),
        (9.223372036854776e18, "9.223372036854776e+18"),
        (1e22, "1e+22"),
        (1e23, "1e+23"),
        (1e100, "1e+100"),
        (1e-100, "1e-100"),
        (5e-324, "5e-324"),
        (2.2250738585072014e-308, "2.2250738585072014e-308"),
        (1.7976931348623157e308, "1.7976931348623157e+308"),
        (-1.7976931348623157e308, "-1.7976931348623157e+308"),
        (1.5e-323, "1.5e-323"),
        (2.5e22, "2.5e+22"),
        (1.152921504606847e18, "1.152921504606847e+18"),
        // exact ties between two shortest candidates: CPython takes the even one, `{:e}` the
        // upper one (`…182.3`, `…488.813`, `…312e-08`)
        (2247721593076182.25, "2247721593076182.2"),
        (-2247721593076182.25, "-2247721593076182.2"),
        (23606692168488.8125, "23606692168488.812"),
        // 2^-25 and 2^-24: below a power of two the lower candidate must still read back; for
        // 2^-24 (`…0625`) it does not, so the odd `…063` stays
        (2.98023223876953125e-08, "2.9802322387695312e-08"),
        (5.9604644775390625e-08, "5.960464477539063e-08"),
        (1.1920928955078125e-07, "1.1920928955078125e-07"),
    ];

    #[test]
    fn writes_edges_like_repr() {
        for (value, expected) in EDGES {
            assert_eq!(text(*value), *expected);
        }
    }

    #[test]
    fn writes_non_finite_like_json_dumps() {
        assert_eq!(text(f64::NAN), "NaN");
        assert_eq!(text(f64::INFINITY), "Infinity");
        assert_eq!(text(f64::NEG_INFINITY), "-Infinity");
    }

    #[test]
    fn appends() {
        let mut out = b"[".to_vec();
        write_float(2.5, &mut out);
        assert_eq!(out, b"[2.5");
    }

    /// `splitmix64`, the same in the generator script.
    fn splitmix(state: &mut u64) -> u64 {
        *state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = *state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    /// 300 000 floats against CPython's `repr`, compared through an FNV-1a hash of all the
    /// reprs, each followed by `\n`. The CPython side (3.11 and 3.13 agree):
    ///
    /// ```python
    /// import struct
    /// M = (1 << 64) - 1
    /// def splitmix(state):
    ///     state = (state + 0x9E3779B97F4A7C15) & M
    ///     z = state
    ///     z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M
    ///     z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M
    ///     return state, z ^ (z >> 31)
    /// def floats(n):
    ///     s = 0
    ///     for i in range(n):
    ///         s, x = splitmix(s)
    ///         k = i % 3
    ///         if k == 0:
    ///             bits = x
    ///         elif k == 1:
    ///             bits = (x & 0x800FFFFFFFFFFFFF) | ((1023 - 30 + (x >> 52) % 100) << 52)
    ///         else:
    ///             v = float(x % 10**((x >> 40) % 18)) / float(f"1e{(x >> 20) % 23}")
    ///             bits = struct.unpack('<Q', struct.pack('<d', v))[0]
    ///         f = struct.unpack('<d', struct.pack('<Q', bits))[0]
    ///         if f == f and f not in (float('inf'), float('-inf')):
    ///             yield f
    /// h = 0xcbf29ce484222325
    /// count = 0
    /// for f in floats(300000):
    ///     for b in repr(f).encode() + b"\n":
    ///         h = ((h ^ b) * 0x100000001b3) & M
    ///     count += 1
    /// print(count, hex(h))  # 299956 0x3804773aec124c4e
    /// ```
    #[test]
    fn writes_random_floats_like_repr() {
        let mut state = 0;
        let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
        let mut count = 0;
        let mut out = Vec::new();
        for i in 0..300_000 {
            let x = splitmix(&mut state);
            let value = match i % 3 {
                // any bit pattern: mostly exponent form
                0 => f64::from_bits(x),
                // a binary exponent in [-30, 70): both notation switches
                1 => f64::from_bits(
                    (x & 0x800F_FFFF_FFFF_FFFF) | ((1023 - 30 + (x >> 52) % 100) << 52),
                ),
                // short decimals: an integer over a power of ten
                _ => {
                    (x % 10u64.pow(((x >> 40) % 18) as u32)) as f64
                        / format!("1e{}", (x >> 20) % 23).parse::<f64>().unwrap()
                }
            };
            if !value.is_finite() {
                continue;
            }
            out.clear();
            write_float(value, &mut out);
            // every repr must round-trip, whatever the hash says
            assert_eq!(
                std::str::from_utf8(&out)
                    .unwrap()
                    .parse::<f64>()
                    .unwrap()
                    .to_bits(),
                value.to_bits()
            );
            for &b in out.iter().chain(b"\n") {
                hash = (hash ^ u64::from(b)).wrapping_mul(0x100_0000_01b3);
            }
            count += 1;
        }
        assert_eq!(count, 299_956);
        assert_eq!(hash, 0x3804_773a_ec12_4c4e);
    }
}
