//! Exposes build metadata to `build_info()` as compile-time env vars.

use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap_or_default()).join("../..");
    let lock = root.join("Cargo.lock");
    let manifest = root.join("Cargo.toml");
    println!("cargo::rerun-if-changed={}", lock.display());
    println!("cargo::rerun-if-changed={}", manifest.display());

    let profile = env::var("PROFILE").unwrap_or_default();
    let cargo_profile = if profile == "debug" {
        "dev"
    } else {
        profile.as_str()
    };
    let lto_override = format!("CARGO_PROFILE_{}_LTO", cargo_profile.to_uppercase());
    println!("cargo::rerun-if-env-changed={lto_override}");
    // ponytail: line scan of our own two files, not a TOML parser; both layouts are cargo-written
    // or ours. An unknown layout yields "unknown", which test_build.py rejects.
    let lto = env::var(&lto_override).ok().unwrap_or_else(|| {
        let text = fs::read_to_string(&manifest).unwrap_or_default();
        section_value(&text, &format!("[profile.{cargo_profile}]"), "lto")
            .unwrap_or_else(|| "false".to_owned())
    });
    let pyo3 = fs::read_to_string(&lock)
        .ok()
        .and_then(|text| locked_version(&text, "pyo3"))
        .unwrap_or_else(|| "unknown".to_owned());

    let version = pep440(&env::var("CARGO_PKG_VERSION").unwrap_or_default());
    println!("cargo::rustc-env=AIOGRAM_CORE_VERSION={version}");
    println!("cargo::rustc-env=AIOGRAM_CORE_PROFILE={profile}");
    println!("cargo::rustc-env=AIOGRAM_CORE_LTO={lto}");
    println!("cargo::rustc-env=AIOGRAM_CORE_PYO3_VERSION={pyo3}");
    println!(
        "cargo::rustc-env=AIOGRAM_CORE_TARGET={}",
        env::var("TARGET").unwrap_or_default()
    );
}

/// PEP 440 form of a crate version, as in `aiogram.__version__`: `4.0.0-alpha.1` -> `4.0.0a1`.
/// The inverse of `cargo_version` in `scripts/bump_version.py`; test_build.py checks they agree.
fn pep440(version: &str) -> String {
    let Some((release, pre)) = version.split_once('-') else {
        return version.to_owned();
    };
    let pre = [("alpha.", "a"), ("beta.", "b"), ("rc.", "rc")]
        .iter()
        .find_map(|(semver, pep)| pre.strip_prefix(semver).map(|n| format!("{pep}{n}")))
        .unwrap_or_else(|| format!("-{pre}"));
    format!("{release}{pre}")
}

/// `key = value` inside `[section]`, with quotes stripped.
fn section_value(text: &str, section: &str, key: &str) -> Option<String> {
    text.lines()
        .map(str::trim)
        .skip_while(|line| *line != section)
        .skip(1)
        .take_while(|line| !line.starts_with('['))
        .find_map(|line| {
            let (k, v) = line.split_once('=')?;
            (k.trim() == key).then(|| v.trim().trim_matches('"').to_owned())
        })
}

/// Version of `name` in `Cargo.lock`.
fn locked_version(text: &str, name: &str) -> Option<String> {
    let mut lines = text.lines();
    let needle = format!("name = \"{name}\"");
    lines.find(|line| *line == needle)?;
    let version = lines.next()?.strip_prefix("version = ")?;
    Some(version.trim_matches('"').to_owned())
}
