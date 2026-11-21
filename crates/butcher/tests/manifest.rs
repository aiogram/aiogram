// clippy.toml's allow-*-in-tests covers #[test] fns only, not the helpers of an integration test crate
#![allow(clippy::unwrap_used)]

use std::path::Path;

use butcher::manifest::{FetchStatus, Manifest};

const FIXTURE: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/manifest.toml");

#[test]
fn round_trip_is_byte_identical() {
    let fixture = std::fs::read_to_string(FIXTURE).unwrap();
    let manifest = Manifest::load(Path::new(FIXTURE)).unwrap();
    assert_eq!(
        manifest.sources.openapi.as_ref().unwrap().status,
        FetchStatus::Unreachable
    );
    assert_eq!(manifest.to_toml().unwrap(), fixture);

    let path = Path::new(env!("CARGO_TARGET_TMPDIR")).join("manifest.toml");
    manifest.write(&path).unwrap();
    assert_eq!(Manifest::load(&path).unwrap(), manifest);
    assert_eq!(std::fs::read_to_string(&path).unwrap(), fixture);
}

#[test]
fn unknown_key_fails_with_its_path() {
    let text = std::fs::read_to_string(FIXTURE).unwrap().replacen(
        "status = \"ok\"",
        "status = \"ok\"\netag = \"x\"",
        1,
    );
    let path = Path::new(env!("CARGO_TARGET_TMPDIR")).join("manifest-unknown.toml");
    std::fs::write(&path, text).unwrap();
    let err = Manifest::load(&path).unwrap_err().to_string();
    assert!(err.contains(": sources.html.etag: "), "{err}");
    assert!(err.contains("unknown field `etag`"), "{err}");
}

#[test]
fn invalid_toml_fails() {
    let path = Path::new(env!("CARGO_TARGET_TMPDIR")).join("manifest-invalid.toml");
    std::fs::write(&path, "api_version = \n").unwrap();
    assert!(matches!(
        Manifest::load(&path),
        Err(butcher::Error::Parse { .. })
    ));
}

fn load_variant(name: &str, from: &str, to: &str) -> Result<Manifest, butcher::Error> {
    let text = std::fs::read_to_string(FIXTURE).unwrap();
    assert!(text.contains(from), "{from}");
    let path = Path::new(env!("CARGO_TARGET_TMPDIR")).join(name);
    std::fs::write(&path, text.replacen(from, to, 1)).unwrap();
    Manifest::load(&path)
}

#[test]
fn fetched_at_must_be_a_utc_datetime() {
    let from = "fetched_at = 2026-11-21T09:30:00Z";
    for (i, to) in [
        "fetched_at = 2026-11-21",
        "fetched_at = 2026-11-21T09:30:00",
        "fetched_at = 2026-11-21T09:30:00+03:00",
    ]
    .into_iter()
    .enumerate()
    {
        let err = load_variant(&format!("manifest-time-{i}.toml"), from, to).unwrap_err();
        assert!(
            err.to_string().contains(": sources.html.fetched_at: "),
            "{err}"
        );
    }
}

#[test]
fn sha256_follows_the_status() {
    let ok_without = load_variant(
        "manifest-ok-no-sha.toml",
        "sha256 = \"5d6e",
        "# sha256 = \"5d6e",
    );
    let err = ok_without.unwrap_err().to_string();
    assert!(err.contains(": sources.html.sha256: "), "{err}");

    let unreachable_with = load_variant(
        "manifest-unreachable-sha.toml",
        "fetched_at = 2026-11-21T09:30:01Z",
        "fetched_at = 2026-11-21T09:30:01Z\nsha256 = \"00\"",
    );
    let err = unreachable_with.unwrap_err().to_string();
    assert!(err.contains(": sources.openapi.sha256: "), "{err}");
}

#[test]
fn an_invalid_manifest_is_not_written() {
    let mut manifest = Manifest::load(Path::new(FIXTURE)).unwrap();
    manifest.sources.html.sha256 = None;
    let err = manifest.to_toml().unwrap_err();
    assert!(err.to_string().contains("sources.html.sha256"), "{err}");
}
