//! `butcher/snapshots/<api_version>/manifest.toml`: where the snapshot's sources came from (D118).
//! C-01 defines the schema; C-02 fills it, C-06 / C-10 compute the overlay / ledger digests.

use std::path::Path;

use serde::{Deserialize, Serialize};
use toml::value::{Datetime, Offset};

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

impl Sources {
    /// Invariants serde cannot express, as `(key path, message)`.
    pub(crate) fn check(&self) -> Result<(), (String, String)> {
        let records = [
            ("html", Some(&self.html)),
            ("preview", self.preview.as_ref()),
            ("openapi", self.openapi.as_ref()),
            ("errors", self.errors.as_ref()),
        ];
        for (name, record) in records {
            let Some(record) = record else { continue };
            let at = |key: &str| format!("sources.{name}.{key}");
            let t = &record.fetched_at;
            if t.date.is_none() || t.time.is_none() || t.offset != Some(Offset::Z) {
                return Err((
                    at("fetched_at"),
                    "must be a UTC date-time (`...Z`)".to_owned(),
                ));
            }
            match (record.status, &record.sha256) {
                (FetchStatus::Ok, None) => {
                    return Err((at("sha256"), "required when status is `ok`".to_owned()));
                }
                (FetchStatus::Unreachable, Some(_)) => {
                    let message = "must be absent when status is `unreachable`";
                    return Err((at("sha256"), message.to_owned()));
                }
                _ => {}
            }
        }
        Ok(())
    }
}

impl Manifest {
    pub fn load(path: &Path) -> Result<Manifest, Error> {
        let text = crate::read(path)?;
        let de = toml::Deserializer::parse(&text).map_err(|e| Error::Parse {
            path: path.to_owned(),
            at: ".".to_owned(),
            message: e.to_string(),
        })?;
        let manifest: Manifest =
            serde_path_to_error::deserialize(de).map_err(|e| crate::parse_error(path, e))?;
        manifest.check().map_err(|e| crate::invalid(path, e))?;
        Ok(manifest)
    }

    /// Invariants serde cannot express, as `(key path, message)`.
    fn check(&self) -> Result<(), (String, String)> {
        self.sources.check()
    }

    pub fn write(&self, path: &Path) -> Result<(), Error> {
        crate::write(path, &self.to_toml()?)
    }

    /// The exact bytes [`Manifest::write`] writes.
    pub fn to_toml(&self) -> Result<String, Error> {
        self.check().map_err(crate::invalid_output)?;
        toml::to_string(self).map_err(|e| Error::Encode(e.to_string()))
    }
}
