//! The `Unknown…` decode hook's process-wide counter (10 §3 "Visibility and strictness"): one
//! count per `(entity, site, value)`, so the caller can log the first occurrence once and expose
//! the rest as metrics. The caller logs after the Rust phase ([`Cursor`](super::Cursor) hands the
//! first occurrences back); nothing here touches Python.

use std::collections::HashMap;
use std::fmt;
use std::sync::{LazyLock, Mutex, PoisonError};

/// Where an `Unknown…` was built.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum Site {
    /// a union tag no variant has
    Tag,
    /// a union member that failed to decode (D107)
    Malformed,
    /// an enum value outside the known set
    Enum,
    /// a top-level `Update` key that is no known update type
    UpdateType,
}

impl fmt::Display for Site {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Tag => "unknown tag",
            Self::Malformed => "malformed member",
            Self::Enum => "unknown enum value",
            Self::UpdateType => "unknown update type",
        })
    }
}

/// One counted key.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub(crate) struct Seen {
    pub(crate) entity: &'static str,
    pub(crate) site: Site,
    /// the tag, enum value or key, at most [`MAX_VALUE`] bytes
    pub(crate) value: Box<str>,
}

impl Seen {
    pub(crate) fn new(entity: &'static str, site: Site, value: &str) -> Self {
        let cut = value.floor_char_boundary(MAX_VALUE);
        Self {
            entity,
            site,
            value: value.get(..cut).unwrap_or_default().into(),
        }
    }
}

/// Distinct keys kept: the values come from untrusted input, so the table must not grow with it.
pub(crate) const MAX_KEYS: usize = 1024;
/// Bytes of a value kept in a key.
pub(crate) const MAX_VALUE: usize = 64;

#[derive(Debug, Default)]
pub(crate) struct Counter {
    keys: HashMap<Seen, u64>,
    /// occurrences of keys past [`MAX_KEYS`]: counted, never "first"
    overflow: u64,
}

impl Counter {
    /// Counts one occurrence; `true` the first time `seen` is counted.
    pub(crate) fn record(&mut self, seen: &Seen) -> bool {
        if let Some(count) = self.keys.get_mut(seen) {
            *count = count.saturating_add(1);
            return false;
        }
        if self.keys.len() >= MAX_KEYS {
            self.overflow = self.overflow.saturating_add(1);
            return false;
        }
        self.keys.insert(seen.clone(), 1);
        true
    }

    pub(crate) fn count(&self, seen: &Seen) -> u64 {
        self.keys.get(seen).copied().unwrap_or(0)
    }

    pub(crate) fn overflow(&self) -> u64 {
        self.overflow
    }
}

static COUNTER: LazyLock<Mutex<Counter>> = LazyLock::new(Mutex::default);

/// Counts one occurrence in the process-wide counter; `true` the first time. A count is per
/// decode attempt: a malformed union member is decoded twice (variant, then shared fields), so a
/// value in its shared fields counts twice; "first" is unaffected.
pub(crate) fn record(seen: &Seen) -> bool {
    COUNTER
        .lock()
        .unwrap_or_else(PoisonError::into_inner)
        .record(seen)
}

/// Every counted key with its count, plus the overflow count (metrics, E-14 / H-01).
pub(crate) fn snapshot() -> (Vec<(Seen, u64)>, u64) {
    let counter = COUNTER.lock().unwrap_or_else(PoisonError::into_inner);
    let keys = counter
        .keys
        .iter()
        .map(|(seen, count)| (seen.clone(), *count))
        .collect();
    (keys, counter.overflow)
}
