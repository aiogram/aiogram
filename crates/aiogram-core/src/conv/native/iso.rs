//! ISO 8601 dates and times.
//!
//! The parsers take a strict subset of what CPython's `date/time/datetime.fromisoformat` accept
//! and give exactly the same values; for anything else they return `None` and the caller falls
//! back to `fromisoformat`, so the accepted set never differs from Python's. The writers give
//! exactly `isoformat(sep, timespec)`.
//!
//! The subset is the extended format only, and only where CPython 3.11 to 3.15 agree:
//!
//! - date: `YYYY-MM-DD`, year 1 to 9999;
//! - time: `HH:MM`, `HH:MM:SS`, `HH:MM:SS.f` with 1 to 6 fraction digits (padded right), hour
//!   0 to 23 (3.14 reads `24:00` as the next midnight, 3.11 rejects it), second 0 to 59;
//! - offset: `Z`, `±HH:MM`, `±HH:MM:SS`, `±HH:MM:SS.f{1,6}`, hours below 24, minutes and
//!   seconds below 60 (3.11 to 3.14 add up a `:60`, 3.15 rejects it), not below one second
//!   unless 0 (3.11 to 3.14 read `+00:00:00.5` as UTC, 3.15 keeps the microseconds);
//! - datetime: the date alone (midnight), or the date, `T` or a space, and a time.
//!
//! Deferred to Python: basic format (`20240101`, `1230`), ISO week dates, `HH` alone, a `,`
//! fraction, a leading `T` on a time, more than 6 fraction digits (CPython truncates),
//! `HH:MM.f` (3.11 to 3.13 only), offsets without colons or with a space before them, any
//! other datetime separator.

use crate::conv::ir::Timespec;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub(crate) struct Date {
    pub(crate) year: i32,
    pub(crate) month: u8,
    pub(crate) day: u8,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub(crate) struct Time {
    pub(crate) hour: u8,
    pub(crate) minute: u8,
    pub(crate) second: u8,
    pub(crate) microsecond: u32,
    /// UTC offset in microseconds (`utcoffset()`); `None` for a naive time
    pub(crate) offset: Option<i64>,
}

/// `YYYY-MM-DD`; `None`: defer to `date.fromisoformat`.
pub(crate) fn parse_date(text: &str) -> Option<Date> {
    let b = text.as_bytes();
    if b.len() != 10 || b[4] != b'-' || b[7] != b'-' {
        return None;
    }
    let year = digits(&b[0..4])?;
    let month = digits(&b[5..7])?;
    let day = digits(&b[8..10])?;
    if year == 0 || !(1..=12).contains(&month) || day == 0 || day > days_in_month(year, month) {
        return None;
    }
    Some(Date {
        year: year as i32,
        month: month as u8,
        day: day as u8,
    })
}

/// `HH:MM[:SS[.ffffff]][Z|±HH:MM[:SS[.ffffff]]]` subset; `None`: defer to `time.fromisoformat`.
pub(crate) fn parse_time(text: &str) -> Option<Time> {
    let (hour, minute, second, microsecond, rest) = parse_hms(text.as_bytes())?;
    if hour > 23 || minute > 59 || second > 59 {
        return None;
    }
    let offset = match rest {
        [] => None,
        [b'Z'] => Some(0),
        [sign @ (b'+' | b'-'), rest @ ..] => {
            let (hours, minutes, seconds, micros, []) = parse_hms(rest)? else {
                return None;
            };
            if hours > 23 || minutes > 59 || seconds > 59 {
                return None;
            }
            let seconds = i64::from(hours * 3600 + minutes * 60 + seconds);
            // a sub-second offset (`+00:00:00.5`): up to 3.14 CPython drops the microseconds
            // when the whole seconds are 0 and returns `timezone.utc`, 3.15 keeps them
            if seconds == 0 && micros != 0 {
                return None;
            }
            let total = seconds * 1_000_000 + i64::from(micros);
            Some(if *sign == b'-' { -total } else { total })
        }
        _ => return None,
    };
    Some(Time {
        hour: hour as u8,
        minute: minute as u8,
        second: second as u8,
        microsecond,
        offset,
    })
}

/// `<date>[T or space]<time>`; `None`: defer to `datetime.fromisoformat`.
pub(crate) fn parse_datetime(text: &str) -> Option<(Date, Time)> {
    let midnight = Time {
        hour: 0,
        minute: 0,
        second: 0,
        microsecond: 0,
        offset: None,
    };
    // `get` rather than slicing: byte 10 may sit inside a multi-byte character
    let date = parse_date(text.get(..10)?)?;
    match text.as_bytes().get(10) {
        None => Some((date, midnight)),
        Some(b'T' | b' ') => Some((date, parse_time(text.get(11..)?)?)),
        Some(_) => None,
    }
}

/// `date.isoformat()`.
pub(crate) fn write_date(date: &Date, out: &mut String) {
    push_padded(out, date.year.unsigned_abs(), 4);
    out.push('-');
    push_padded(out, u32::from(date.month), 2);
    out.push('-');
    push_padded(out, u32::from(date.day), 2);
}

/// `time.isoformat(timespec)`, with the offset when the time is aware.
pub(crate) fn write_time(time: &Time, timespec: Timespec, out: &mut String) {
    let timespec = match timespec {
        Timespec::Auto if time.microsecond != 0 => Timespec::Microseconds,
        Timespec::Auto => Timespec::Seconds,
        other => other,
    };
    push_padded(out, u32::from(time.hour), 2);
    if timespec != Timespec::Hours {
        out.push(':');
        push_padded(out, u32::from(time.minute), 2);
    }
    if matches!(
        timespec,
        Timespec::Seconds | Timespec::Milliseconds | Timespec::Microseconds
    ) {
        out.push(':');
        push_padded(out, u32::from(time.second), 2);
    }
    if timespec == Timespec::Milliseconds {
        // truncated, not rounded, as CPython does
        out.push('.');
        push_padded(out, time.microsecond / 1000, 3);
    } else if timespec == Timespec::Microseconds {
        out.push('.');
        push_padded(out, time.microsecond, 6);
    }
    if let Some(offset) = time.offset {
        write_offset(offset, out);
    }
}

/// `datetime.isoformat(sep, timespec)`.
pub(crate) fn write_datetime(
    date: &Date,
    time: &Time,
    sep: char,
    timespec: Timespec,
    out: &mut String,
) {
    write_date(date, out);
    out.push(sep);
    write_time(time, timespec, out);
}

/// `+HH:MM[:SS[.ffffff]]` as `isoformat` writes a UTC offset: the sign, then the absolute value
/// (`-05:30:15.500000` for `-timedelta(seconds=19815.5)`).
pub(crate) fn write_offset(offset: i64, out: &mut String) {
    let total = offset.unsigned_abs();
    let micro = (total % 1_000_000) as u32;
    let seconds = (total / 1_000_000) as u32;
    out.push(if offset < 0 { '-' } else { '+' });
    push_padded(out, seconds / 3600, 2);
    out.push(':');
    push_padded(out, (seconds / 60) % 60, 2);
    if !seconds.is_multiple_of(60) || micro != 0 {
        out.push(':');
        push_padded(out, seconds % 60, 2);
        if micro != 0 {
            out.push('.');
            push_padded(out, micro, 6);
        }
    }
}

/// Days since 1970-01-01 of a proleptic Gregorian date (negative before it).
pub(crate) fn days_from_civil(year: i32, month: u8, day: u8) -> i64 {
    // H. Hinnant's `days_from_civil`: years start on March 1, so the leap day ends a year
    let year = i64::from(year) - i64::from(month <= 2);
    let era = year.div_euclid(400);
    let year_of_era = year - era * 400;
    let month_from_march = (i64::from(month) + 9) % 12;
    let day_of_year = (153 * month_from_march + 2) / 5 + i64::from(day) - 1;
    let day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    era * 146_097 + day_of_era - 719_468
}

/// The proleptic Gregorian date `days` after 1970-01-01; the inverse of [`days_from_civil`].
pub(crate) fn civil_from_days(days: i64) -> Date {
    let days = days + 719_468;
    let era = days.div_euclid(146_097);
    let day_of_era = days - era * 146_097;
    let year_of_era =
        (day_of_era - day_of_era / 1460 + day_of_era / 36_524 - day_of_era / 146_096) / 365;
    let day_of_year = day_of_era - (365 * year_of_era + year_of_era / 4 - year_of_era / 100);
    let month_from_march = (5 * day_of_year + 2) / 153;
    let day = day_of_year - (153 * month_from_march + 2) / 5 + 1;
    let month = if month_from_march < 10 {
        month_from_march + 3
    } else {
        month_from_march - 9
    };
    let year = year_of_era + era * 400 + i64::from(month <= 2);
    Date {
        year: year as i32,
        month: month as u8,
        day: day as u8,
    }
}

/// `HH:MM[:SS[.f{1,6}]]` and the bytes after it, unvalidated; the microseconds are padded right.
fn parse_hms(b: &[u8]) -> Option<(u32, u32, u32, u32, &[u8])> {
    if b.len() < 5 || b[2] != b':' {
        return None;
    }
    let hour = digits(&b[0..2])?;
    let minute = digits(&b[3..5])?;
    let mut rest = &b[5..];
    let (mut second, mut micro) = (0, 0);
    if let [b':', s1, s2, tail @ ..] = rest {
        second = digits(&[*s1, *s2])?;
        rest = tail;
        if let [b'.', tail @ ..] = rest {
            let n = tail.iter().take_while(|c| c.is_ascii_digit()).count();
            if !(1..=6).contains(&n) {
                return None;
            }
            micro = digits(&tail[..n])? * 10u32.pow(6 - n as u32);
            rest = &tail[n..];
        }
    }
    Some((hour, minute, second, micro, rest))
}

/// The value of a run of ASCII digits; `None` when any byte is not one.
fn digits(b: &[u8]) -> Option<u32> {
    b.iter().try_fold(0u32, |acc, &c| {
        c.is_ascii_digit().then(|| acc * 10 + u32::from(c - b'0'))
    })
}

fn days_in_month(year: u32, month: u32) -> u32 {
    match month {
        2 if year.is_multiple_of(4) && (!year.is_multiple_of(100) || year.is_multiple_of(400)) => {
            29
        }
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

/// Append `value` in decimal, zero-padded to at least `width` digits (`%0*d`).
fn push_padded(out: &mut String, value: u32, width: usize) {
    let mut buf = [b'0'; 10];
    let mut start = buf.len();
    let mut n = value;
    loop {
        start -= 1;
        buf[start] = b'0' + (n % 10) as u8;
        n /= 10;
        if n == 0 {
            break;
        }
    }
    for &b in &buf[start.min(buf.len().saturating_sub(width))..] {
        out.push(char::from(b));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const fn d(year: i32, month: u8, day: u8) -> Date {
        Date { year, month, day }
    }

    const fn t(hour: u8, minute: u8, second: u8, microsecond: u32, offset: Option<i64>) -> Time {
        Time {
            hour,
            minute,
            second,
            microsecond,
            offset,
        }
    }

    const SPECS: [Timespec; 6] = [
        Timespec::Auto,
        Timespec::Hours,
        Timespec::Minutes,
        Timespec::Seconds,
        Timespec::Milliseconds,
        Timespec::Microseconds,
    ];

    // Generated with CPython 3.11 `fromisoformat` (the same on 3.14 and 3.15 for every entry
    // that is not deferred); `None` is what the parser must return, with CPython's own value
    // in a comment when the parser defers a text CPython accepts.
    const TIMES: &[(&str, Option<Time>)] = &[
        ("00:00", Some(t(0, 0, 0, 0, None))),
        ("23:59", Some(t(23, 59, 0, 0, None))),
        ("12:30:45", Some(t(12, 30, 45, 0, None))),
        ("23:59:59.999999", Some(t(23, 59, 59, 999999, None))),
        ("12:30:45.1", Some(t(12, 30, 45, 100000, None))),
        ("12:30:45.12", Some(t(12, 30, 45, 120000, None))),
        ("12:30:45.123", Some(t(12, 30, 45, 123000, None))),
        ("12:30:45.1234", Some(t(12, 30, 45, 123400, None))),
        ("12:30:45.12345", Some(t(12, 30, 45, 123450, None))),
        ("12:30:45.123456", Some(t(12, 30, 45, 123456, None))),
        ("12:30:45.000000", Some(t(12, 30, 45, 0, None))),
        ("12:30Z", Some(t(12, 30, 0, 0, Some(0)))),
        ("12:30:45Z", Some(t(12, 30, 45, 0, Some(0)))),
        ("12:30:45.5Z", Some(t(12, 30, 45, 500000, Some(0)))),
        ("12:30+05:30", Some(t(12, 30, 0, 0, Some(19800000000)))),
        ("12:30-05:30", Some(t(12, 30, 0, 0, Some(-19800000000)))),
        (
            "12:30:45+05:30:15",
            Some(t(12, 30, 45, 0, Some(19815000000))),
        ),
        (
            "12:30:45-05:30:15",
            Some(t(12, 30, 45, 0, Some(-19815000000))),
        ),
        (
            "12:30:45+05:30:15.5",
            Some(t(12, 30, 45, 0, Some(19815500000))),
        ),
        (
            "12:30:45-05:30:15.5",
            Some(t(12, 30, 45, 0, Some(-19815500000))),
        ),
        (
            "12:30:45-05:30:15.000001",
            Some(t(12, 30, 45, 0, Some(-19815000001))),
        ),
        (
            "12:30:45+23:59:59.999999",
            Some(t(12, 30, 45, 0, Some(86399999999))),
        ),
        (
            "12:30:45-23:59:59.999999",
            Some(t(12, 30, 45, 0, Some(-86399999999))),
        ),
        ("12:30:45+00:00", Some(t(12, 30, 45, 0, Some(0)))),
        ("12:30:45-00:00", Some(t(12, 30, 45, 0, Some(0)))),
        (
            "12:30+00:00:00.000001",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, Some(0))) */
        ),
        (
            "12:30-00:00:00.5",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, Some(0))) */
        ),
        ("12:30+00:00:01.5", Some(t(12, 30, 0, 0, Some(1500000)))),
        ("12:30-00:01", Some(t(12, 30, 0, 0, Some(-60000000)))),
        ("24:00", None),
        ("24:00:00", None),
        ("12:60", None),
        ("12:30:60", None),
        ("12:30:61", None),
        ("25:00", None),
        (
            "12", None, /* deferred; CPython 3.11: Some(t(12, 0, 0, 0, None)) */
        ),
        (
            "1230", None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, None)) */
        ),
        (
            "12:30:45,5",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 45, 500000, None)) */
        ),
        ("12:30:45.", None),
        (
            "12:30:45.1234567",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 45, 123456, None)) */
        ),
        (
            "12:30.5", None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 500000, None)) */
        ),
        ("12:30:45z", None),
        (
            "12:30:45+05",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 45, 0, Some(18000000000))) */
        ),
        (
            "12:30:45+0530",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 45, 0, Some(19800000000))) */
        ),
        (
            "12:30:45 +05:30",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 45, 0, Some(19800000000))) */
        ),
        ("12:30:45+24:00", None),
        (
            "12:30+05:60",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, Some(21600000000))) */
        ),
        (
            "12:30+05:30:60",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, Some(19860000000))) */
        ),
        ("12:30+05:30:15.", None),
        (
            "12:30+05:30:15.1234567",
            None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, Some(19815123456))) */
        ),
        ("12:30+5:30", None),
        ("12:3a", None),
        ("12:30:4", None),
        ("1:30", None),
        ("12:30:45Z+01:00", None),
        ("12:30Zx", None),
        ("", None),
        (
            "T12:30", None, /* deferred; CPython 3.11: Some(t(12, 30, 0, 0, None)) */
        ),
        ("12:30:45.123+05:30x", None),
        ("١٢:30", None),
    ];
    const DATES: &[(&str, Option<Date>)] = &[
        ("2024-02-29", Some(d(2024, 2, 29))),
        ("2023-02-29", None),
        ("1900-02-29", None),
        ("2000-02-29", Some(d(2000, 2, 29))),
        ("0001-01-01", Some(d(1, 1, 1))),
        ("9999-12-31", Some(d(9999, 12, 31))),
        ("2024-04-31", None),
        ("2024-04-30", Some(d(2024, 4, 30))),
        ("2024-12-31", Some(d(2024, 12, 31))),
        ("2024-01-32", None),
        ("2024-00-10", None),
        ("2024-13-01", None),
        ("0000-01-01", None),
        ("2024-1-01", None),
        (
            "20240101", None, /* deferred; CPython 3.11: Some(d(2024, 1, 1)) */
        ),
        (
            "2024-W01", None, /* deferred; CPython 3.11: Some(d(2024, 1, 1)) */
        ),
        (
            "2024-W01-1",
            None, /* deferred; CPython 3.11: Some(d(2024, 1, 1)) */
        ),
        ("+2024-01-01", None),
        ("2024-01-01 ", None),
        ("2024/01/01", None),
        ("", None),
        ("2024-01-0١", None),
    ];
    const DATETIMES: &[(&str, Option<(Date, Time)>)] = &[
        ("2024-01-01", Some((d(2024, 1, 1), t(0, 0, 0, 0, None)))),
        (
            "2024-01-01T12:30",
            Some((d(2024, 1, 1), t(12, 30, 0, 0, None))),
        ),
        (
            "2024-01-01 12:30",
            Some((d(2024, 1, 1), t(12, 30, 0, 0, None))),
        ),
        (
            "2024-01-01T12:30:45.123456+05:30",
            Some((d(2024, 1, 1), t(12, 30, 45, 123456, Some(19800000000)))),
        ),
        (
            "2024-02-29T23:59:59.999999-23:59:59.999999",
            Some((d(2024, 2, 29), t(23, 59, 59, 999999, Some(-86399999999)))),
        ),
        (
            "2024-01-01T12:30:45Z",
            Some((d(2024, 1, 1), t(12, 30, 45, 0, Some(0)))),
        ),
        (
            "2024-01-01t12:30",
            None, /* deferred; CPython 3.11: Some((d(2024, 1, 1), t(12, 30, 0, 0, None))) */
        ),
        (
            "2024-01-01x12:30",
            None, /* deferred; CPython 3.11: Some((d(2024, 1, 1), t(12, 30, 0, 0, None))) */
        ),
        (
            "2024-01-01é12:30",
            None, /* deferred; CPython 3.11: Some((d(2024, 1, 1), t(12, 30, 0, 0, None))) */
        ),
        ("2024-01-01T", None),
        (
            "2024-01-01T12",
            None, /* deferred; CPython 3.11: Some((d(2024, 1, 1), t(12, 0, 0, 0, None))) */
        ),
        ("2024-01-01T24:00", None),
        ("2024-02-30T00:00", None),
        (
            "20240101T123045",
            None, /* deferred; CPython 3.11: Some((d(2024, 1, 1), t(12, 30, 45, 0, None))) */
        ),
        (
            "2024-01-01T12:30:45.1234567",
            None, /* deferred; CPython 3.11: Some((d(2024, 1, 1), t(12, 30, 45, 123456, None))) */
        ),
        ("2024-01-01  12:30", None),
        ("2024-01-01T12:30 ", None),
        ("٢٠٢٤-01-01", None),
    ];

    // CPython `isoformat`, in the order of SPECS
    const TIME_WRITES: &[(Time, [&str; 6])] = &[
        (
            t(1, 2, 3, 0, None),
            [
                "01:02:03",
                "01",
                "01:02",
                "01:02:03",
                "01:02:03.000",
                "01:02:03.000000",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(0)),
            [
                "01:02:03+00:00",
                "01+00:00",
                "01:02+00:00",
                "01:02:03+00:00",
                "01:02:03.000+00:00",
                "01:02:03.000000+00:00",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(19800000000)),
            [
                "01:02:03+05:30",
                "01+05:30",
                "01:02+05:30",
                "01:02:03+05:30",
                "01:02:03.000+05:30",
                "01:02:03.000000+05:30",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(-19800000000)),
            [
                "01:02:03-05:30",
                "01-05:30",
                "01:02-05:30",
                "01:02:03-05:30",
                "01:02:03.000-05:30",
                "01:02:03.000000-05:30",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(-19815500000)),
            [
                "01:02:03-05:30:15.500000",
                "01-05:30:15.500000",
                "01:02-05:30:15.500000",
                "01:02:03-05:30:15.500000",
                "01:02:03.000-05:30:15.500000",
                "01:02:03.000000-05:30:15.500000",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(-1)),
            [
                "01:02:03-00:00:00.000001",
                "01-00:00:00.000001",
                "01:02-00:00:00.000001",
                "01:02:03-00:00:00.000001",
                "01:02:03.000-00:00:00.000001",
                "01:02:03.000000-00:00:00.000001",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(1)),
            [
                "01:02:03+00:00:00.000001",
                "01+00:00:00.000001",
                "01:02+00:00:00.000001",
                "01:02:03+00:00:00.000001",
                "01:02:03.000+00:00:00.000001",
                "01:02:03.000000+00:00:00.000001",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(86399999999)),
            [
                "01:02:03+23:59:59.999999",
                "01+23:59:59.999999",
                "01:02+23:59:59.999999",
                "01:02:03+23:59:59.999999",
                "01:02:03.000+23:59:59.999999",
                "01:02:03.000000+23:59:59.999999",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(-86399999999)),
            [
                "01:02:03-23:59:59.999999",
                "01-23:59:59.999999",
                "01:02-23:59:59.999999",
                "01:02:03-23:59:59.999999",
                "01:02:03.000-23:59:59.999999",
                "01:02:03.000000-23:59:59.999999",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(-30000000)),
            [
                "01:02:03-00:00:30",
                "01-00:00:30",
                "01:02-00:00:30",
                "01:02:03-00:00:30",
                "01:02:03.000-00:00:30",
                "01:02:03.000000-00:00:30",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(3600000000)),
            [
                "01:02:03+01:00",
                "01+01:00",
                "01:02+01:00",
                "01:02:03+01:00",
                "01:02:03.000+01:00",
                "01:02:03.000000+01:00",
            ],
        ),
        (
            t(1, 2, 3, 0, Some(59000001)),
            [
                "01:02:03+00:00:59.000001",
                "01+00:00:59.000001",
                "01:02+00:00:59.000001",
                "01:02:03+00:00:59.000001",
                "01:02:03.000+00:00:59.000001",
                "01:02:03.000000+00:00:59.000001",
            ],
        ),
        (
            t(1, 2, 3, 4500, None),
            [
                "01:02:03.004500",
                "01",
                "01:02",
                "01:02:03",
                "01:02:03.004",
                "01:02:03.004500",
            ],
        ),
        (
            t(1, 2, 3, 4500, Some(0)),
            [
                "01:02:03.004500+00:00",
                "01+00:00",
                "01:02+00:00",
                "01:02:03+00:00",
                "01:02:03.004+00:00",
                "01:02:03.004500+00:00",
            ],
        ),
        (
            t(1, 2, 3, 4500, Some(19800000000)),
            [
                "01:02:03.004500+05:30",
                "01+05:30",
                "01:02+05:30",
                "01:02:03+05:30",
                "01:02:03.004+05:30",
                "01:02:03.004500+05:30",
            ],
        ),
        (
            t(1, 2, 3, 4500, Some(-19800000000)),
            [
                "01:02:03.004500-05:30",
                "01-05:30",
                "01:02-05:30",
                "01:02:03-05:30",
                "01:02:03.004-05:30",
                "01:02:03.004500-05:30",
            ],
        ),
        (
            t(1, 2, 3, 4500, Some(-19815500000)),
            [
                "01:02:03.004500-05:30:15.500000",
                "01-05:30:15.500000",
                "01:02-05:30:15.500000",
                "01:02:03-05:30:15.500000",
                "01:02:03.004-05:30:15.500000",
                "01:02:03.004500-05:30:15.500000",
            ],
        ),
        (
            t(1, 2, 3, 4500, Some(-1)),
            [
                "01:02:03.004500-00:00:00.000001",
                "01-00:00:00.000001",
                "01:02-00:00:00.000001",
                "01:02:03-00:00:00.000001",
                "01:02:03.004-00:00:00.000001",
                "01:02:03.004500-00:00:00.000001",
            ],
        ),
        (
            t(1, 2, 3, 999999, None),
            [
                "01:02:03.999999",
                "01",
                "01:02",
                "01:02:03",
                "01:02:03.999",
                "01:02:03.999999",
            ],
        ),
        (
            t(1, 2, 3, 999999, Some(0)),
            [
                "01:02:03.999999+00:00",
                "01+00:00",
                "01:02+00:00",
                "01:02:03+00:00",
                "01:02:03.999+00:00",
                "01:02:03.999999+00:00",
            ],
        ),
        (
            t(1, 2, 3, 999999, Some(19800000000)),
            [
                "01:02:03.999999+05:30",
                "01+05:30",
                "01:02+05:30",
                "01:02:03+05:30",
                "01:02:03.999+05:30",
                "01:02:03.999999+05:30",
            ],
        ),
        (
            t(1, 2, 3, 999999, Some(-19800000000)),
            [
                "01:02:03.999999-05:30",
                "01-05:30",
                "01:02-05:30",
                "01:02:03-05:30",
                "01:02:03.999-05:30",
                "01:02:03.999999-05:30",
            ],
        ),
        (
            t(1, 2, 3, 999999, Some(-19815500000)),
            [
                "01:02:03.999999-05:30:15.500000",
                "01-05:30:15.500000",
                "01:02-05:30:15.500000",
                "01:02:03-05:30:15.500000",
                "01:02:03.999-05:30:15.500000",
                "01:02:03.999999-05:30:15.500000",
            ],
        ),
        (
            t(1, 2, 3, 999999, Some(-1)),
            [
                "01:02:03.999999-00:00:00.000001",
                "01-00:00:00.000001",
                "01:02-00:00:00.000001",
                "01:02:03-00:00:00.000001",
                "01:02:03.999-00:00:00.000001",
                "01:02:03.999999-00:00:00.000001",
            ],
        ),
        (
            t(1, 2, 3, 1000, None),
            [
                "01:02:03.001000",
                "01",
                "01:02",
                "01:02:03",
                "01:02:03.001",
                "01:02:03.001000",
            ],
        ),
        (
            t(1, 2, 3, 1000, Some(0)),
            [
                "01:02:03.001000+00:00",
                "01+00:00",
                "01:02+00:00",
                "01:02:03+00:00",
                "01:02:03.001+00:00",
                "01:02:03.001000+00:00",
            ],
        ),
        (
            t(1, 2, 3, 1000, Some(19800000000)),
            [
                "01:02:03.001000+05:30",
                "01+05:30",
                "01:02+05:30",
                "01:02:03+05:30",
                "01:02:03.001+05:30",
                "01:02:03.001000+05:30",
            ],
        ),
        (
            t(1, 2, 3, 1000, Some(-19800000000)),
            [
                "01:02:03.001000-05:30",
                "01-05:30",
                "01:02-05:30",
                "01:02:03-05:30",
                "01:02:03.001-05:30",
                "01:02:03.001000-05:30",
            ],
        ),
        (
            t(1, 2, 3, 1000, Some(-19815500000)),
            [
                "01:02:03.001000-05:30:15.500000",
                "01-05:30:15.500000",
                "01:02-05:30:15.500000",
                "01:02:03-05:30:15.500000",
                "01:02:03.001-05:30:15.500000",
                "01:02:03.001000-05:30:15.500000",
            ],
        ),
        (
            t(1, 2, 3, 1000, Some(-1)),
            [
                "01:02:03.001000-00:00:00.000001",
                "01-00:00:00.000001",
                "01:02-00:00:00.000001",
                "01:02:03-00:00:00.000001",
                "01:02:03.001-00:00:00.000001",
                "01:02:03.001000-00:00:00.000001",
            ],
        ),
        (
            t(1, 2, 3, 999, None),
            [
                "01:02:03.000999",
                "01",
                "01:02",
                "01:02:03",
                "01:02:03.000",
                "01:02:03.000999",
            ],
        ),
        (
            t(1, 2, 3, 999, Some(0)),
            [
                "01:02:03.000999+00:00",
                "01+00:00",
                "01:02+00:00",
                "01:02:03+00:00",
                "01:02:03.000+00:00",
                "01:02:03.000999+00:00",
            ],
        ),
        (
            t(1, 2, 3, 999, Some(19800000000)),
            [
                "01:02:03.000999+05:30",
                "01+05:30",
                "01:02+05:30",
                "01:02:03+05:30",
                "01:02:03.000+05:30",
                "01:02:03.000999+05:30",
            ],
        ),
        (
            t(1, 2, 3, 999, Some(-19800000000)),
            [
                "01:02:03.000999-05:30",
                "01-05:30",
                "01:02-05:30",
                "01:02:03-05:30",
                "01:02:03.000-05:30",
                "01:02:03.000999-05:30",
            ],
        ),
        (
            t(1, 2, 3, 999, Some(-19815500000)),
            [
                "01:02:03.000999-05:30:15.500000",
                "01-05:30:15.500000",
                "01:02-05:30:15.500000",
                "01:02:03-05:30:15.500000",
                "01:02:03.000-05:30:15.500000",
                "01:02:03.000999-05:30:15.500000",
            ],
        ),
        (
            t(1, 2, 3, 999, Some(-1)),
            [
                "01:02:03.000999-00:00:00.000001",
                "01-00:00:00.000001",
                "01:02-00:00:00.000001",
                "01:02:03-00:00:00.000001",
                "01:02:03.000-00:00:00.000001",
                "01:02:03.000999-00:00:00.000001",
            ],
        ),
    ];
    const DATETIME_WRITES: &[(Date, Time, char, [&str; 6])] = &[
        (
            d(1, 1, 1),
            t(0, 0, 0, 0, None),
            'T',
            [
                "0001-01-01T00:00:00",
                "0001-01-01T00",
                "0001-01-01T00:00",
                "0001-01-01T00:00:00",
                "0001-01-01T00:00:00.000",
                "0001-01-01T00:00:00.000000",
            ],
        ),
        (
            d(9999, 12, 31),
            t(23, 59, 59, 999999, Some(-86399999999)),
            'T',
            [
                "9999-12-31T23:59:59.999999-23:59:59.999999",
                "9999-12-31T23-23:59:59.999999",
                "9999-12-31T23:59-23:59:59.999999",
                "9999-12-31T23:59:59-23:59:59.999999",
                "9999-12-31T23:59:59.999-23:59:59.999999",
                "9999-12-31T23:59:59.999999-23:59:59.999999",
            ],
        ),
        (
            d(5, 1, 2),
            t(3, 4, 5, 999999, None),
            'x',
            [
                "0005-01-02x03:04:05.999999",
                "0005-01-02x03",
                "0005-01-02x03:04",
                "0005-01-02x03:04:05",
                "0005-01-02x03:04:05.999",
                "0005-01-02x03:04:05.999999",
            ],
        ),
        (
            d(2024, 2, 29),
            t(12, 0, 0, 123000, Some(0)),
            'é',
            [
                "2024-02-29é12:00:00.123000+00:00",
                "2024-02-29é12+00:00",
                "2024-02-29é12:00+00:00",
                "2024-02-29é12:00:00+00:00",
                "2024-02-29é12:00:00.123+00:00",
                "2024-02-29é12:00:00.123000+00:00",
            ],
        ),
        (
            d(2024, 2, 29),
            t(12, 0, 0, 1, Some(19800000000)),
            ' ',
            [
                "2024-02-29 12:00:00.000001+05:30",
                "2024-02-29 12+05:30",
                "2024-02-29 12:00+05:30",
                "2024-02-29 12:00:00+05:30",
                "2024-02-29 12:00:00.000+05:30",
                "2024-02-29 12:00:00.000001+05:30",
            ],
        ),
    ];
    const EPOCH_DAYS: &[(Date, i64)] = &[
        (d(1, 1, 1), -719162),
        (d(9999, 12, 31), 2932896),
        (d(1970, 1, 1), 0),
        (d(1969, 12, 31), -1),
        (d(2000, 2, 29), 11016),
        (d(1600, 3, 1), -135080),
        (d(2604, 5, 28), 231711),
        (d(4254, 9, 1), 834457),
        (d(4311, 8, 8), 855251),
        (d(1451, 9, 27), -189292),
        (d(2218, 9, 5), 90827),
        (d(8094, 11, 5), 2237054),
        (d(503, 9, 27), -535542),
        (d(979, 3, 27), -361870),
        (d(1572, 6, 15), -145201),
        (d(2842, 7, 8), 318680),
        (d(9317, 3, 31), 2683526),
        (d(5815, 11, 7), 1404667),
        (d(2405, 8, 23), 159115),
        (d(4602, 8, 9), 961538),
        (d(7371, 12, 21), 1973029),
        (d(348, 11, 19), -592101),
        (d(5273, 7, 7), 1206584),
        (d(5598, 2, 20), 1325150),
        (d(5204, 8, 7), 1181413),
        (d(4485, 2, 5), 918621),
    ];

    #[test]
    fn parses_like_cpython() {
        for (text, expected) in TIMES {
            assert_eq!(parse_time(text), *expected, "time {text:?}");
        }
        for (text, expected) in DATES {
            assert_eq!(parse_date(text), *expected, "date {text:?}");
        }
        for (text, expected) in DATETIMES {
            assert_eq!(parse_datetime(text), *expected, "datetime {text:?}");
        }
    }

    #[test]
    fn writes_like_cpython() {
        for (time, expected) in TIME_WRITES {
            for (spec, text) in SPECS.iter().zip(expected) {
                let mut out = String::new();
                write_time(time, *spec, &mut out);
                assert_eq!(out, *text, "{time:?} {spec:?}");
            }
        }
        for (date, time, sep, expected) in DATETIME_WRITES {
            for (spec, text) in SPECS.iter().zip(expected) {
                let mut out = String::new();
                write_datetime(date, time, *sep, *spec, &mut out);
                assert_eq!(out, *text, "{date:?} {time:?} {spec:?}");
            }
        }
    }

    #[test]
    fn written_text_parses_back() {
        for (time, _) in TIME_WRITES {
            let mut out = String::new();
            write_time(time, Timespec::Auto, &mut out);
            // the parser defers sub-second offsets, see `parse_time`
            if time.offset.is_some_and(|o| o.abs() < 1_000_000 && o != 0) {
                assert_eq!(parse_time(&out), None, "{out}");
            } else {
                assert_eq!(parse_time(&out), Some(*time), "{out}");
            }
        }
    }

    #[test]
    fn epoch_days_match_cpython() {
        for (date, days) in EPOCH_DAYS {
            assert_eq!(
                days_from_civil(date.year, date.month, date.day),
                *days,
                "{date:?}"
            );
            assert_eq!(civil_from_days(*days), *date, "{days}");
        }
    }

    #[test]
    fn epoch_days_cover_every_date() {
        // every day of 0001-01-01..=9999-12-31 round-trips, in order, and parses as a valid date
        let first = days_from_civil(1, 1, 1);
        let mut previous = d(0, 12, 31);
        for days in first..=days_from_civil(9999, 12, 31) {
            let date = civil_from_days(days);
            let key = |x: Date| (x.year, x.month, x.day);
            assert!(key(date) > key(previous), "{date:?}");
            assert_eq!(days_from_civil(date.year, date.month, date.day), days);
            assert_eq!(
                parse_date(&{
                    let mut text = String::new();
                    write_date(&date, &mut text);
                    text
                }),
                Some(date)
            );
            previous = date;
        }
        assert_eq!(previous, d(9999, 12, 31));
    }
}
