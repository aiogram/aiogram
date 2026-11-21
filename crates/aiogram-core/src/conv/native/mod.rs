//! Pure-Rust text formats used by the native kinds: no Python API in here, so `cargo test`
//! covers them without an interpreter.
//!
//! - [`uuid`]: canonical / hex UUID text;
//! - [`iso`]: ISO 8601 dates and times, as `fromisoformat` reads them and `isoformat` writes them;
//! - [`base64`]: padded standard and unpadded url-safe base64;
//! - [`number`]: JSON numbers as Python's `repr(float)` writes them;
//! - [`string`]: JSON string escaping, as `json.dumps(ensure_ascii=False)` writes it.

pub(crate) mod base64;
pub(crate) mod iso;
pub(crate) mod number;
pub(crate) mod string;
pub(crate) mod uuid;
