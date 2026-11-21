//! `butcher fetch`: download the Bot API sources into a content-addressed cache (D118, C-02).
//! HTTP happens only here; every later step reads the cache (or a bundle unpacked into it).
//!
//! Layout of the cache directory: `<sha256>` holds one raw source, `fetch.toml` is the
//! [`Fetched`] index (which URL produced which digest, when, with which status).

use std::path::{Path, PathBuf};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use toml::value::{Date, Datetime, Offset, Time};

use crate::Error;
use crate::manifest::{FetchStatus, SourceRecord, Sources};

pub const DEFAULT_CACHE: &str = "target/butcher-cache";
pub const INDEX: &str = "fetch.toml";
pub const HTML_URL: &str = "https://core.telegram.org/bots/api";
// `corefork.` serves the JSON files today; `core.` answers with the HTML page (02 §6).
pub const OPENAPI_URL: &str = "https://corefork.telegram.org/bots/api.json";
pub const ERRORS_URL: &str = "https://corefork.telegram.org/bots/errors.json";

const MAX_BODY: u64 = 64 << 20;

/// What a fetch produced: the `sources` table of the snapshot manifest plus the tool version.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Fetched {
    /// `crates/butcher` package version that fetched.
    pub butcher: String,
    pub sources: Sources,
}

impl Fetched {
    pub fn to_toml(&self) -> Result<String, Error> {
        toml::to_string(self).map_err(|e| Error::Encode(e.to_string()))
    }

    pub fn from_toml(path: &Path, text: &str) -> Result<Fetched, Error> {
        let de = toml::Deserializer::parse(text).map_err(|e| Error::Parse {
            path: path.to_owned(),
            at: ".".to_owned(),
            message: e.to_string(),
        })?;
        serde_path_to_error::deserialize(de).map_err(|e| crate::parse_error(path, e))
    }

    /// Reads the cache index and checks that every `ok` source is in the cache and matches its digest.
    pub fn load(cache: &Path) -> Result<Fetched, Error> {
        let path = cache.join(INDEX);
        let fetched = Fetched::from_toml(&path, &crate::read(&path)?)?;
        for (_, record) in fetched.records() {
            if let Some(sha) = &record.sha256 {
                let blob = cache.join(sha);
                let bytes = std::fs::read(&blob).map_err(|source| Error::Io {
                    path: blob.clone(),
                    source,
                })?;
                if sha256(&bytes) != *sha {
                    return Err(Error::Fetch(format!(
                        "{}: content does not match its name",
                        blob.display()
                    )));
                }
            }
        }
        Ok(fetched)
    }

    /// The present records with their manifest key.
    pub fn records(&self) -> Vec<(&'static str, &SourceRecord)> {
        let s = &self.sources;
        [
            ("html", Some(&s.html)),
            ("preview", s.preview.as_ref()),
            ("openapi", s.openapi.as_ref()),
            ("errors", s.errors.as_ref()),
        ]
        .into_iter()
        .filter_map(|(name, record)| Some((name, record?)))
        .collect()
    }
}

#[derive(Debug, Clone)]
pub struct Options {
    pub html: String,
    pub preview: Option<String>,
    pub openapi: String,
    pub errors: String,
    pub cache: PathBuf,
    /// Tries per source; a transport error or a 5xx is retried.
    pub attempts: u32,
    pub backoff: Duration,
    pub timeout: Duration,
}

impl Default for Options {
    fn default() -> Self {
        Options {
            html: HTML_URL.to_owned(),
            preview: None,
            openapi: OPENAPI_URL.to_owned(),
            errors: ERRORS_URL.to_owned(),
            cache: PathBuf::from(DEFAULT_CACHE),
            attempts: 3,
            backoff: Duration::from_secs(2),
            timeout: Duration::from_secs(30),
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Kind {
    Html,
    Json,
}

/// Fetches every source into the cache and writes the index. The HTML page is the one source
/// a snapshot cannot do without; any other source that cannot be had is recorded `unreachable`.
pub fn fetch(opts: &Options) -> Result<Fetched, Error> {
    std::fs::create_dir_all(&opts.cache).map_err(|source| Error::Io {
        path: opts.cache.clone(),
        source,
    })?;
    let agent = agent(opts.timeout);
    let one = |url: &str, kind| record(opts, &agent, url, kind);
    let html = one(&opts.html, Kind::Html)?;
    if html.status != FetchStatus::Ok {
        return Err(Error::Fetch(format!(
            "{}: the Bot API page is unreachable (http status {:?})",
            opts.html, html.http_status
        )));
    }
    let preview = opts
        .preview
        .as_deref()
        .map(|u| one(u, Kind::Html))
        .transpose()?;
    let fetched = Fetched {
        butcher: env!("CARGO_PKG_VERSION").to_owned(),
        sources: Sources {
            html,
            preview,
            openapi: Some(one(&opts.openapi, Kind::Json)?),
            errors: Some(one(&opts.errors, Kind::Json)?),
        },
    };
    let index = opts.cache.join(INDEX);
    crate::write(&index, &fetched.to_toml()?)?;
    Ok(fetched)
}

fn agent(timeout: Duration) -> ureq::Agent {
    ureq::Agent::config_builder()
        .timeout_global(Some(timeout))
        .http_status_as_error(false)
        .build()
        .into()
}

struct Got {
    status: u16,
    content_type: String,
    body: Vec<u8>,
}

fn get(agent: &ureq::Agent, url: &str) -> Result<Got, String> {
    let response = agent.get(url).call().map_err(|e| e.to_string())?;
    let status = response.status().as_u16();
    let content_type = response
        .headers()
        .get("content-type")
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default()
        .to_ascii_lowercase();
    let body = response
        .into_body()
        .with_config()
        .limit(MAX_BODY)
        .read_to_vec()
        .map_err(|e| e.to_string())?;
    Ok(Got {
        status,
        content_type,
        body,
    })
}

fn record(
    opts: &Options,
    agent: &ureq::Agent,
    url: &str,
    kind: Kind,
) -> Result<SourceRecord, Error> {
    let mut last = None;
    for attempt in 0..opts.attempts.max(1) {
        if attempt > 0 {
            std::thread::sleep(opts.backoff * attempt);
        }
        match get(agent, url) {
            Ok(got) if got.status >= 500 => last = Some(got.status),
            Ok(got) => return finish(&opts.cache, url, kind, got),
            Err(_) => last = None,
        }
    }
    Ok(unreachable_record(url, last))
}

fn finish(cache: &Path, url: &str, kind: Kind, got: Got) -> Result<SourceRecord, Error> {
    if !usable(kind, &got) {
        return Ok(unreachable_record(url, Some(got.status)));
    }
    let sha = sha256(&got.body);
    let blob = cache.join(&sha);
    if !blob.exists() {
        std::fs::write(&blob, &got.body).map_err(|source| Error::Io { path: blob, source })?;
    }
    Ok(SourceRecord {
        url: url.to_owned(),
        status: FetchStatus::Ok,
        http_status: Some(got.status),
        fetched_at: now(),
        sha256: Some(sha),
    })
}

/// A 2xx, and for a JSON source not the HTML page the host serves instead (02 §6): judged by
/// the content type and by the first byte, because either alone has been wrong.
fn usable(kind: Kind, got: &Got) -> bool {
    if !(200..300).contains(&got.status) {
        return false;
    }
    if kind == Kind::Html {
        return true;
    }
    let first = got.body.iter().find(|b| !b.is_ascii_whitespace());
    !got.content_type.contains("html") && first != Some(&b'<')
}

fn unreachable_record(url: &str, http_status: Option<u16>) -> SourceRecord {
    SourceRecord {
        url: url.to_owned(),
        status: FetchStatus::Unreachable,
        http_status,
        fetched_at: now(),
        sha256: None,
    }
}

pub fn sha256(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

fn now() -> Datetime {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_or(0, |d| d.as_secs());
    utc(secs)
}

/// Unix seconds -> `YYYY-MM-DDTHH:MM:SSZ` (civil-from-days, H. Hinnant).
fn utc(secs: u64) -> Datetime {
    let (days, rem) = (secs / 86_400, secs % 86_400);
    let z = days + 719_468;
    let era = z / 146_097;
    let doe = z % 146_097;
    let yoe = (doe - doe / 1_460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = yoe + era * 400 + u64::from(month <= 2);
    Datetime {
        date: Some(Date {
            year: year as u16,
            month: month as u8,
            day: day as u8,
        }),
        time: Some(Time {
            hour: (rem / 3600) as u8,
            minute: (rem % 3600 / 60) as u8,
            second: Some((rem % 60) as u8),
            nanosecond: None,
        }),
        offset: Some(Offset::Z),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn utc_matches_known_instants() {
        assert_eq!(utc(0).to_string(), "1970-01-01T00:00:00Z");
        assert_eq!(utc(951_782_400).to_string(), "2000-02-29T00:00:00Z");
        assert_eq!(
            utc(1_795_219_200 + 3_661).to_string(),
            "2026-11-21T01:01:01Z"
        );
    }

    #[test]
    fn sha256_of_empty_input() {
        assert_eq!(
            sha256(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }
}
