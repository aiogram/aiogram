//! butcher: the reproducible Bot API generator (v4/research/02 §5), run as `cargo xtask butcher <cmd>`.

use std::fmt;
use std::path::{Path, PathBuf};

pub mod bundle;
pub mod cli;
pub mod fetch;
pub mod ir;
pub mod manifest;

#[derive(Debug)]
pub enum Error {
    Io {
        path: PathBuf,
        source: std::io::Error,
    },
    /// A file that does not match the schema. `at` is the key path (`types[0].fields[2].foo`).
    Parse {
        path: PathBuf,
        at: String,
        message: String,
    },
    Encode(String),
    /// A source that cannot be fetched, a bundle that does not verify.
    Fetch(String),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Io { path, source } => write!(f, "{}: {source}", path.display()),
            Error::Parse { path, at, message } => {
                write!(f, "{}: {at}: {message}", path.display())
            }
            Error::Encode(message) => write!(f, "encode: {message}"),
            Error::Fetch(message) => write!(f, "fetch: {message}"),
        }
    }
}

impl std::error::Error for Error {}

pub(crate) fn read(path: &Path) -> Result<String, Error> {
    std::fs::read_to_string(path).map_err(|source| Error::Io {
        path: path.to_owned(),
        source,
    })
}

pub(crate) fn write(path: &Path, text: &str) -> Result<(), Error> {
    std::fs::write(path, text).map_err(|source| Error::Io {
        path: path.to_owned(),
        source,
    })
}

pub(crate) fn invalid(path: &Path, (at, message): (String, String)) -> Error {
    Error::Parse {
        path: path.to_owned(),
        at,
        message,
    }
}

/// A value about to be written breaks an invariant `load` would reject.
pub(crate) fn invalid_output((at, message): (String, String)) -> Error {
    Error::Encode(format!("{at}: {message}"))
}

pub(crate) fn parse_error<E: fmt::Display>(path: &Path, e: serde_path_to_error::Error<E>) -> Error {
    Error::Parse {
        path: path.to_owned(),
        at: e.path().to_string(),
        message: e.inner().to_string(),
    }
}
