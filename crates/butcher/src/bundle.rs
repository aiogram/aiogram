//! Raw source bundles (D118): a `tar.gz` of the cache (`manifest.toml` + one `<sha256>` file per
//! source) attached to a release, so `build --offline` reproduces a snapshot without the live page.

use std::io::Read;
use std::path::Path;

use flate2::Compression;
use flate2::read::GzDecoder;
use flate2::write::GzEncoder;

use crate::Error;
use crate::fetch::{Fetched, INDEX, sha256};

const MANIFEST: &str = "manifest.toml";

fn io(path: &Path, source: std::io::Error) -> Error {
    Error::Io {
        path: path.to_owned(),
        source,
    }
}

/// Packs the cached sources. Same cache, same bytes: entries are sorted and carry no mtime or owner.
pub fn pack(cache: &Path, out: &Path) -> Result<(), Error> {
    let fetched = Fetched::load(cache)?;
    let mut shas: Vec<&String> = fetched
        .records()
        .into_iter()
        .filter_map(|(_, r)| r.sha256.as_ref())
        .collect();
    shas.sort();
    shas.dedup();

    let file = std::fs::File::create(out).map_err(|e| io(out, e))?;
    let mut tar = tar::Builder::new(GzEncoder::new(file, Compression::default()));
    let mut add = |name: &str, bytes: &[u8]| {
        let mut header = tar::Header::new_gnu();
        header.set_size(bytes.len() as u64);
        header.set_mode(0o644);
        header.set_mtime(0);
        tar.append_data(&mut header, name, bytes)
    };
    add(MANIFEST, fetched.to_toml()?.as_bytes()).map_err(|e| io(out, e))?;
    for sha in shas {
        let blob = cache.join(sha);
        let bytes = std::fs::read(&blob).map_err(|e| io(&blob, e))?;
        add(sha, &bytes).map_err(|e| io(out, e))?;
    }
    let gz = tar.into_inner().map_err(|e| io(out, e))?;
    gz.finish().map_err(|e| io(out, e))?;
    Ok(())
}

/// Unpacks a bundle into `cache` and returns what it holds. The bundle is untrusted: only
/// `manifest.toml` and files named by the sha256 of their own content are accepted.
pub fn unpack(bundle: &Path, cache: &Path) -> Result<Fetched, Error> {
    let file = std::fs::File::open(bundle).map_err(|e| io(bundle, e))?;
    let mut blobs = Vec::new();
    let mut manifest = None;
    let mut archive = tar::Archive::new(GzDecoder::new(file));
    for entry in archive.entries().map_err(|e| io(bundle, e))? {
        let mut entry = entry.map_err(|e| io(bundle, e))?;
        let name = entry
            .path()
            .map_err(|e| io(bundle, e))?
            .to_string_lossy()
            .into_owned();
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes).map_err(|e| io(bundle, e))?;
        if name == MANIFEST {
            manifest = Some(bytes);
        } else if sha256(&bytes) == name {
            blobs.push((name, bytes));
        } else {
            return Err(Error::Fetch(format!(
                "{}: entry `{name}` is not `{MANIFEST}` or a file named by its sha256",
                bundle.display()
            )));
        }
    }
    let Some(manifest) = manifest else {
        return Err(Error::Fetch(format!(
            "{}: no `{MANIFEST}`",
            bundle.display()
        )));
    };
    let text = String::from_utf8(manifest)
        .map_err(|e| Error::Fetch(format!("{}: {MANIFEST}: {e}", bundle.display())))?;
    // nothing is written unless the manifest parses and the bundle holds every source it names
    let fetched = Fetched::from_toml(&bundle.join(MANIFEST), &text)?;
    for (name, record) in fetched.records() {
        if let Some(sha) = &record.sha256
            && !blobs.iter().any(|(n, _)| n == sha)
        {
            return Err(Error::Fetch(format!(
                "{}: sources.{name} names {sha}, which the bundle does not hold",
                bundle.display()
            )));
        }
    }

    std::fs::create_dir_all(cache).map_err(|e| io(cache, e))?;
    for (name, bytes) in blobs {
        let path = cache.join(name);
        std::fs::write(&path, bytes).map_err(|e| io(&path, e))?;
    }
    let index = cache.join(INDEX);
    crate::write(&index, &text)?;
    Fetched::load(cache)
}
