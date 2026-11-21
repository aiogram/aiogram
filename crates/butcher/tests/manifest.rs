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
