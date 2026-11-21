//! `butcher/snapshots/<api_version>/manifest.toml`: where the snapshot's sources came from (D118).
//! C-01 defines the schema; C-02 fills it, C-06 / C-10 compute the overlay / ledger digests.

use std::path::Path;

use serde::{Deserialize, Serialize};
use toml::value::Datetime;

use crate::Error;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Manifest {
    pub api_version: String,
    /// `crates/butcher` package version that wrote the snapshot.
    pub butcher: String,
    pub html_only: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub overlay_sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ledger_sha256: Option<String>,
    pub sources: Sources,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Sources {
    pub html: SourceRecord,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preview: Option<SourceRecord>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub openapi: Option<SourceRecord>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub errors: Option<SourceRecord>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceRecord {
    pub url: String,
    pub status: FetchStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub http_status: Option<u16>,
    /// UTC.
    pub fetched_at: Datetime,
    /// Absent when unreachable.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sha256: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FetchStatus {
    Ok,
    /// No response, or HTML served at a JSON URL (C-02).
    Unreachable,
}

impl Manifest {
    pub fn load(path: &Path) -> Result<Manifest, Error> {
        let text = crate::read(path)?;
        let de = toml::Deserializer::parse(&text).map_err(|e| Error::Parse {
            path: path.to_owned(),
            at: ".".to_owned(),
            message: e.to_string(),
        })?;
        serde_path_to_error::deserialize(de).map_err(|e| crate::parse_error(path, e))
    }

    pub fn write(&self, path: &Path) -> Result<(), Error> {
        crate::write(path, &self.to_toml()?)
    }

    /// The exact bytes [`Manifest::write`] writes.
    pub fn to_toml(&self) -> Result<String, Error> {
        toml::to_string(self).map_err(|e| Error::Encode(e.to_string()))
    }
}
