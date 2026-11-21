// clippy.toml's allow-*-in-tests covers #[test] fns only, not the helpers of an integration test crate
#![allow(clippy::unwrap_used)]

//! `fetch`, the cache, bundles. Every request goes to a server on 127.0.0.1 started by the test.

use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use butcher::bundle;
use butcher::cli::{BuildArgs, Command, FetchArgs, run};
use butcher::fetch::{self, Fetched, INDEX, Options, sha256};
use butcher::manifest::FetchStatus;

#[derive(Clone)]
struct Reply(u16, &'static str, &'static str);

const PAGE: Reply = Reply(200, "text/html; charset=utf-8", "<html>Bot API</html>");
const JSON: Reply = Reply(200, "application/json", "{\"a\":1}");
const JSON2: Reply = Reply(200, "application/json", "{\"errors\":[]}");

struct Server {
    base: String,
    hits: Arc<Mutex<HashMap<String, usize>>>,
}

impl Server {
    /// Each path answers with its replies in order, then keeps repeating the last one.
    fn start(routes: &[(&str, Vec<Reply>)]) -> Server {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let base = format!("http://{}", listener.local_addr().unwrap());
        let hits = Arc::new(Mutex::new(HashMap::new()));
        let routes: HashMap<String, Vec<Reply>> = routes
            .iter()
            .map(|(p, r)| ((*p).to_owned(), r.clone()))
            .collect();
        let seen = Arc::clone(&hits);
        std::thread::spawn(move || {
            for stream in listener.incoming() {
                let mut stream = stream.unwrap();
                let mut request = Vec::new();
                let mut buf = [0u8; 1024];
                while !request.windows(4).any(|w| w == b"\r\n\r\n") {
                    let n = stream.read(&mut buf).unwrap();
                    if n == 0 {
                        break;
                    }
                    request.extend_from_slice(&buf[..n]);
                }
                let request = String::from_utf8_lossy(&request).into_owned();
                let path = request.split_whitespace().nth(1).unwrap_or("/").to_owned();
                let n = {
                    let mut hits = seen.lock().unwrap();
                    let n = hits.entry(path.clone()).or_insert(0);
                    *n += 1;
                    *n
                };
                let Reply(status, ctype, body) = match routes.get(&path) {
                    Some(replies) => replies[(n - 1).min(replies.len() - 1)].clone(),
                    None => Reply(404, "text/plain", "nope"),
                };
                let head = format!(
                    "HTTP/1.1 {status} X\r\nContent-Type: {ctype}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                    body.len()
                );
                let _ = stream.write_all(head.as_bytes());
                let _ = stream.write_all(body.as_bytes());
            }
        });
        Server { base, hits }
    }

    fn url(&self, path: &str) -> String {
        format!("{}{path}", self.base)
    }

    fn hits(&self, path: &str) -> usize {
        self.hits.lock().unwrap().get(path).copied().unwrap_or(0)
    }

    fn options(&self, cache: &Path) -> Options {
        Options {
            html: self.url("/bots/api"),
            preview: None,
            openapi: self.url("/bots/api.json"),
            errors: self.url("/bots/errors.json"),
            cache: cache.to_owned(),
            attempts: 3,
            backoff: Duration::from_millis(1),
            timeout: Duration::from_secs(5),
        }
    }
}

fn happy() -> Server {
    Server::start(&[
        ("/bots/api", vec![PAGE]),
        ("/bots/api.json", vec![JSON]),
        ("/bots/errors.json", vec![JSON2]),
    ])
}

fn scratch(name: &str) -> PathBuf {
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR"))
        .join("fetch")
        .join(name);
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

#[test]
fn fetch_fills_the_cache_and_the_index() {
    let server = happy();
    let cache = scratch("ok").join("cache");
    let fetched = fetch::fetch(&server.options(&cache)).unwrap();

    let s = &fetched.sources;
    assert_eq!(s.html.status, FetchStatus::Ok);
    assert_eq!(s.html.http_status, Some(200));
    assert_eq!(s.html.sha256, Some(sha256(PAGE.2.as_bytes())));
    assert!(s.preview.is_none());
    let openapi = s.openapi.as_ref().unwrap();
    assert_eq!(openapi.sha256, Some(sha256(JSON.2.as_bytes())));
    assert!(openapi.fetched_at.to_string().ends_with('Z'));
    assert_eq!(
        std::fs::read(cache.join(sha256(JSON2.2.as_bytes()))).unwrap(),
        JSON2.2.as_bytes()
    );
    assert_eq!(Fetched::load(&cache).unwrap(), fetched);
    assert_eq!(fetched.butcher, env!("CARGO_PKG_VERSION"));
}

#[test]
fn html_at_a_json_url_is_unreachable_not_a_parse_error() {
    let server = Server::start(&[
        ("/bots/api", vec![PAGE]),
        // by content type
        ("/bots/api.json", vec![Reply(200, "text/html", "{}")]),
        // by first byte, behind whitespace, with an honest-looking content type
        (
            "/bots/errors.json",
            vec![Reply(200, "application/json", "\n <!doctype html>")],
        ),
    ]);
    let cache = scratch("fallback");
    let fetched = fetch::fetch(&server.options(&cache)).unwrap();
    for record in [&fetched.sources.openapi, &fetched.sources.errors] {
        let record = record.as_ref().unwrap();
        assert_eq!(record.status, FetchStatus::Unreachable);
        assert_eq!(record.http_status, Some(200));
        assert_eq!(record.sha256, None);
    }
    // nothing but the page and the index landed in the cache
    assert_eq!(std::fs::read_dir(&cache).unwrap().count(), 2);
}

#[test]
fn a_missing_json_source_is_recorded_a_missing_page_is_an_error() {
    let server = Server::start(&[("/bots/api", vec![PAGE])]);
    let cache = scratch("missing");
    let fetched = fetch::fetch(&server.options(&cache)).unwrap();
    let errors = fetched.sources.errors.unwrap();
    assert_eq!(
        (errors.status, errors.http_status),
        (FetchStatus::Unreachable, Some(404))
    );

    let server = Server::start(&[("/bots/api.json", vec![JSON])]);
    let err = fetch::fetch(&server.options(&scratch("nopage")))
        .unwrap_err()
        .to_string();
    assert!(err.contains("the Bot API page is unreachable"), "{err}");
    assert!(err.contains("404"), "{err}");
}

#[test]
fn server_errors_are_retried_then_recorded() {
    let server = Server::start(&[
        ("/bots/api", vec![PAGE]),
        (
            "/bots/api.json",
            vec![
                Reply(503, "text/plain", "busy"),
                Reply(502, "text/plain", "busy"),
                JSON,
            ],
        ),
        ("/bots/errors.json", vec![Reply(500, "text/plain", "down")]),
    ]);
    let fetched = fetch::fetch(&server.options(&scratch("retry"))).unwrap();
    assert_eq!(fetched.sources.openapi.unwrap().status, FetchStatus::Ok);
    assert_eq!(server.hits("/bots/api.json"), 3);
    let errors = fetched.sources.errors.unwrap();
    assert_eq!(
        (errors.status, errors.http_status),
        (FetchStatus::Unreachable, Some(500))
    );
    assert_eq!(server.hits("/bots/errors.json"), 3);
    assert_eq!(server.hits("/bots/api"), 1);
}

#[test]
fn a_dead_host_is_unreachable_without_a_status() {
    let server = happy();
    let mut opts = server.options(&scratch("dead"));
    let port = TcpListener::bind("127.0.0.1:0")
        .unwrap()
        .local_addr()
        .unwrap()
        .port();
    opts.errors = format!("http://127.0.0.1:{port}/e.json"); // the listener is gone: refused
    opts.attempts = 0; // still tries once
    let errors = fetch::fetch(&opts).unwrap().sources.errors.unwrap();
    assert_eq!(
        (errors.status, errors.http_status),
        (FetchStatus::Unreachable, None)
    );
}

#[test]
fn preview_is_fetched_and_equal_bodies_share_a_blob() {
    let server = Server::start(&[
        ("/bots/api", vec![PAGE]),
        ("/preview", vec![PAGE]),
        ("/bots/api.json", vec![JSON]),
        ("/bots/errors.json", vec![JSON]),
    ]);
    let cache = scratch("preview");
    let mut opts = server.options(&cache);
    opts.preview = Some(server.url("/preview"));
    let fetched = fetch::fetch(&opts).unwrap();
    assert_eq!(
        fetched.sources.preview.as_ref().unwrap().sha256,
        fetched.sources.html.sha256
    );
    assert_eq!(std::fs::read_dir(&cache).unwrap().count(), 3); // page, json, index
}

#[test]
fn bundle_round_trip_reproduces_the_digests() {
    let server = happy();
    let dir = scratch("bundle");
    let cache = dir.join("a");
    let fetched = fetch::fetch(&server.options(&cache)).unwrap();

    let (one, two) = (dir.join("1.tar.gz"), dir.join("2.tar.gz"));
    bundle::pack(&cache, &one).unwrap();
    bundle::pack(&cache, &two).unwrap();
    assert_eq!(std::fs::read(&one).unwrap(), std::fs::read(&two).unwrap());

    // "a second machine": a fresh cache, no server involved
    let other = dir.join("b");
    assert_eq!(bundle::unpack(&one, &other).unwrap(), fetched);
    assert_eq!(
        std::fs::read_to_string(other.join(INDEX)).unwrap(),
        fetched.to_toml().unwrap()
    );
    // and the bundle made from that cache is the same bytes
    let three = dir.join("3.tar.gz");
    bundle::pack(&other, &three).unwrap();
    assert_eq!(std::fs::read(&one).unwrap(), std::fs::read(&three).unwrap());
}

fn tar_gz(path: &Path, entries: &[(&str, &[u8])]) {
    let gz = flate2::write::GzEncoder::new(
        std::fs::File::create(path).unwrap(),
        flate2::Compression::default(),
    );
    let mut tar = tar::Builder::new(gz);
    for (name, bytes) in entries {
        let mut header = tar::Header::new_gnu();
        header.set_size(bytes.len() as u64);
        header.set_mode(0o644);
        tar.append_data(&mut header, name, *bytes).unwrap();
    }
    tar.into_inner().unwrap().finish().unwrap();
}

fn manifest_for(html: &str) -> String {
    format!(
        "butcher = \"0.1.0\"\n\n[sources.html]\nurl = \"u\"\nstatus = \"ok\"\nhttp_status = 200\nfetched_at = 2026-11-21T00:00:00Z\nsha256 = \"{html}\"\n"
    )
}

#[test]
fn a_bad_bundle_is_rejected() {
    let dir = scratch("bad");
    let cache = dir.join("cache");
    let page = sha256(b"page");
    let good = manifest_for(&page);
    type Case<'a> = (&'a str, Vec<(&'a str, &'a [u8])>, &'a str);
    let no_sha = manifest_for(&page).replace(&format!("sha256 = \"{page}\"\n"), "");
    let cases: [Case; 7] = [
        (
            "nosha",
            vec![("manifest.toml", no_sha.as_bytes())],
            "sources.html.sha256: required",
        ),
        (
            "stray",
            vec![("manifest.toml", good.as_bytes()), ("sub/evil", b"x")],
            "not `manifest.toml`",
        ),
        (
            "nomanifest",
            vec![(page.as_str(), b"page")],
            "no `manifest.toml`",
        ),
        ("missing", vec![("manifest.toml", good.as_bytes())], &page),
        (
            "utf8",
            vec![("manifest.toml", &[0xff, 0xfe])],
            "manifest.toml: invalid utf-8",
        ),
        (
            "garbage",
            vec![("manifest.toml", b"not toml =")],
            "manifest.toml",
        ),
        (
            "unknown",
            vec![("manifest.toml", b"butcher = \"x\"\nextra = 1\n")],
            "unknown field `extra`",
        ),
    ];
    for (name, entries, want) in cases {
        let path = dir.join(format!("{name}.tar.gz"));
        tar_gz(&path, &entries);
        let err = bundle::unpack(&path, &cache).unwrap_err().to_string();
        assert!(err.contains(want), "{name}: {err}");
    }
    assert!(
        !cache.join(INDEX).exists(),
        "a rejected manifest must not reach the cache"
    );

    let err = bundle::unpack(&dir.join("absent.tar.gz"), &cache)
        .unwrap_err()
        .to_string();
    assert!(err.contains("absent.tar.gz"), "{err}");
    let not_gz = dir.join("plain");
    std::fs::write(&not_gz, "plain text").unwrap();
    assert!(bundle::unpack(&not_gz, &cache).is_err());
}

#[test]
fn a_tampered_or_missing_cache_is_rejected() {
    let server = happy();
    let cache = scratch("tamper");
    let fetched = fetch::fetch(&server.options(&cache)).unwrap();
    let blob = cache.join(fetched.sources.html.sha256.unwrap());

    std::fs::write(&blob, "changed").unwrap();
    let err = Fetched::load(&cache).unwrap_err().to_string();
    assert!(err.contains("does not match its name"), "{err}");
    assert!(bundle::pack(&cache, &cache.join("x.tar.gz")).is_err());

    std::fs::remove_file(&blob).unwrap();
    assert!(Fetched::load(&cache).is_err());
    assert!(Fetched::load(&cache.join("none")).is_err());
}

#[test]
fn unwritable_places_are_io_errors() {
    let server = happy();
    let dir = scratch("io");
    let file = dir.join("file");
    std::fs::write(&file, "").unwrap();
    // the cache directory is a file
    assert!(fetch::fetch(&server.options(&file)).is_err());
    // the bundle goes into a directory that is not there
    let cache = dir.join("cache");
    fetch::fetch(&server.options(&cache)).unwrap();
    assert!(bundle::pack(&cache, &dir.join("no/such/dir/b.tar.gz")).is_err());
    // the unpack target is a file
    let packed = dir.join("b.tar.gz");
    bundle::pack(&cache, &packed).unwrap();
    assert!(bundle::unpack(&packed, &file).is_err());
}

#[test]
fn cli_fetch_then_build_offline() {
    let server = happy();
    let dir = scratch("cli");
    let args = |bundle: Option<PathBuf>| FetchArgs {
        html: server.url("/bots/api"),
        preview: None,
        openapi: server.url("/bots/api.json"),
        errors: server.url("/bots/errors.json"),
        cache: dir.join("cache"),
        bundle,
    };
    run(Command::Fetch(args(Some(dir.join("b.tar.gz"))))).unwrap();
    assert!(dir.join("b.tar.gz").exists());

    let build = |offline: Option<PathBuf>, cache: &str| {
        run(Command::Build(BuildArgs {
            cache: dir.join(cache),
            offline,
        }))
        .unwrap_err()
    };
    // sources resolve (cache, then bundle); the build itself belongs to C-03..C-08
    assert!(build(None, "cache").contains("build: not implemented"));
    assert!(build(Some(dir.join("b.tar.gz")), "elsewhere").contains("build: not implemented"));
    assert!(dir.join("elsewhere").join(INDEX).exists());
    // no cache and no bundle: a source error, never a network call
    assert!(build(None, "empty").contains("empty/fetch.toml"));

    // the page is gone
    let mut dead = args(None);
    dead.html = server.url("/nope");
    assert!(
        run(Command::Fetch(dead))
            .unwrap_err()
            .contains("unreachable")
    );
}

#[test]
fn refetch_repairs_a_truncated_blob() {
    let server = happy();
    let cache = scratch("repair");
    let fetched = fetch::fetch(&server.options(&cache)).unwrap();
    let blob = cache.join(fetched.sources.html.sha256.as_ref().unwrap());
    std::fs::write(&blob, "trunc").unwrap();
    assert!(Fetched::load(&cache).is_err());
    fetch::fetch(&server.options(&cache)).unwrap();
    assert!(Fetched::load(&cache).is_ok());
}
