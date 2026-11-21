// clippy.toml's allow-*-in-tests covers #[test] fns only, not the helpers of an integration test crate
#![allow(clippy::unwrap_used)]

use std::path::{Path, PathBuf};

use butcher::Error;
use butcher::ir::{Ir, Placeholder};
use butcher::sources::errors::{Parsed, from_str, literal_len, parse};
use regex::Regex;

const INPUT: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/errors.json");
const EXPECTED: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/ir.errors.json");

fn parsed(text: &str) -> Result<Parsed, Error> {
    from_str(text, Path::new("errors.json"))
}

fn with_errors(messages: &str) -> String {
    format!(r#"{{"version": "1", "errors": {{"400": {{{messages}}}}}}}"#)
}

/// Exact message first, then the matching template with the longest literal; `None` if two tie.
fn lookup<'a>(ir: &'a Ir, message: &str) -> Option<&'a str> {
    if let Some(e) = ir
        .errors
        .iter()
        .find(|e| e.message == message && e.template.is_none())
    {
        return Some(&e.message);
    }
    let hits: Vec<_> = ir
        .errors
        .iter()
        .filter(|e| {
            e.template
                .as_ref()
                .is_some_and(|t| Regex::new(&t.regex).unwrap().is_match(message))
        })
        .collect();
    let best = hits.iter().map(|e| literal_len(&e.message)).max()?;
    let mut top = hits.iter().filter(|e| literal_len(&e.message) == best);
    let first = top.next()?;
    top.next().is_none().then_some(first.message.as_str())
}

fn render(message: &str) -> String {
    message.replace("%s", "abc").replace("%d", "42")
}

/// Every template matches its own rendering, with the one most specific winner; every exact message is its own winner.
fn check_catalogue(ir: &Ir) {
    for e in &ir.errors {
        let text = if e.template.is_some() {
            render(&e.message)
        } else {
            e.message.clone()
        };
        assert_eq!(lookup(ir, &text), Some(e.message.as_str()), "{}", e.message);
        if let Some(t) = &e.template {
            let caps = Regex::new(&t.regex).unwrap().captures(&text).unwrap();
            assert_eq!(caps.len() - 1, t.placeholders.len());
        }
    }
}

#[test]
fn fixture_output_is_byte_identical() {
    let a = parse(Path::new(INPUT)).unwrap();
    assert!(a.warnings.is_empty());
    let json = a.ir.to_json().unwrap();
    assert_eq!(json, parse(Path::new(INPUT)).unwrap().ir.to_json().unwrap());
    if std::env::var_os("BUTCHER_BLESS").is_some() {
        std::fs::write(EXPECTED, &json).unwrap();
    }
    assert_eq!(json, std::fs::read_to_string(EXPECTED).unwrap());
    let path = PathBuf::from(env!("CARGO_TARGET_TMPDIR")).join("errors-rt.json");
    a.ir.write(&path).unwrap();
    assert_eq!(Ir::load(&path).unwrap(), a.ir);
}

#[test]
fn fixture_catalogue_is_unambiguous() {
    let ir = parse(Path::new(INPUT)).unwrap().ir;
    check_catalogue(&ir);
    // an exact message that a template also matches stays exact
    let tricky = "Bad Request: wrong remote file identifier specified: can't unserialize it";
    assert_eq!(lookup(&ir, tricky), Some(tricky));
    // the longer literal wins over `entity %s`
    let long = "Bad Request: entity begins after the end of the text at UTF-16 offset 5";
    assert_eq!(
        lookup(&ir, long),
        Some("Bad Request: entity begins after the end of the text at UTF-16 offset %d")
    );
    assert_eq!(
        lookup(&ir, "Bad Request: entity bold"),
        Some("Bad Request: entity %s")
    );
    assert_eq!(lookup(&ir, "nope"), None);
}

#[test]
fn placeholder_kinds() {
    let ir = parsed(&with_errors(
        r#""Bad Request: a %s": [], "Bad Request: b %d": [], "Bad Request: c %d/%s": []"#,
    ))
    .unwrap()
    .ir;
    let t = |i: usize| ir.errors[i].template.clone().unwrap();
    assert_eq!(t(0).placeholders, [Placeholder::S]);
    assert_eq!(t(0).regex, "^Bad Request: a (.*?)$");
    assert_eq!(t(1).placeholders, [Placeholder::D]);
    assert_eq!(t(1).regex, r"^Bad Request: b (-?\d+)$");
    assert_eq!(t(2).placeholders, [Placeholder::D, Placeholder::S]);
    let re = Regex::new(&t(1).regex).unwrap();
    assert!(re.is_match("Bad Request: b -7") && !re.is_match("Bad Request: b x"));
    assert!(Regex::new(&t(0).regex).unwrap().is_match("Bad Request: a "));
}

#[test]
fn regex_escapes_syntax_characters() {
    let ir = parsed(&with_errors(r#""x (a.b) [1+1] %d": []"#))
        .unwrap()
        .ir;
    let re = Regex::new(&ir.errors[0].template.clone().unwrap().regex).unwrap();
    assert!(re.is_match("x (a.b) [1+1] 3") && !re.is_match("x (aXb) [1+1] 3"));
}

#[test]
fn mtproto_only_when_unique() {
    let ir = parse(Path::new(INPUT)).unwrap().ir;
    let get = |m: &str| ir.errors.iter().find(|e| e.message == m).unwrap();
    assert_eq!(
        get("Bad Request: ADMINS_TOO_MUCH").mtproto.as_deref(),
        Some("ADMINS_TOO_MUCH")
    );
    assert_eq!(get("Bad Request: chat not found").mtproto, None);
    assert_eq!(get("Forbidden: bot was blocked by the user").code, 403);
    assert_eq!(ir.header.api_version, "10.4");
}

#[test]
fn unknown_top_level_key_warns() {
    let text = r#"{"version": "1", "errors": {}, "new_key": 1, "mtproto_errors": {"Bad Request: gone": ["X"]}}"#;
    let p = parsed(text).unwrap();
    assert!(p.ir.errors.is_empty());
    assert_eq!(p.warnings.len(), 2);
    assert!(p.warnings[0].contains("new_key") && p.warnings[1].contains("gone"));
}

#[test]
fn bad_input_is_rejected_with_a_path() {
    let at = |text: &str| match parsed(text) {
        Err(Error::Parse { at, .. }) => at,
        _ => panic!("expected a parse error"),
    };
    assert_eq!(at("{"), ".");
    assert_eq!(at("[]"), ".");
    assert_eq!(at(r#"{"errors": {}}"#), ".");
    assert_eq!(
        at(r#"{"version": "1", "errors": {"400": {"m": 1}}}"#),
        "errors.400.m"
    );
    assert!(at(&with_errors(r#""Bad Request: 100%": []"#)).starts_with("errors.400"));
    assert!(parse(Path::new("/nonexistent/errors.json")).is_err());
}

/// Live check, `BUTCHER_LIVE=1 cargo test -p butcher errors_counts -- --ignored`. The file comes from
/// `BUTCHER_ERRORS_JSON`, otherwise it is downloaded with `curl` (fetching stays with xtask, C-02).
#[test]
#[ignore = "needs BUTCHER_LIVE=1 and the network"]
fn errors_counts() {
    if std::env::var_os("BUTCHER_LIVE").is_none() {
        return;
    }
    let path = match std::env::var_os("BUTCHER_ERRORS_JSON") {
        Some(p) => PathBuf::from(p),
        None => {
            let p = PathBuf::from(env!("CARGO_TARGET_TMPDIR")).join("live-errors.json");
            let ok = std::process::Command::new("curl")
                .args(["-fsS", "-m", "60", "-o"])
                .arg(&p)
                .arg("https://corefork.telegram.org/bots/errors.json")
                .status()
                .unwrap()
                .success();
            assert!(ok, "curl failed");
            p
        }
    };
    let ir = parse(&path).unwrap().ir;
    let templates = ir.errors.iter().filter(|e| e.template.is_some()).count();
    assert_eq!((ir.errors.len(), templates), (962, 38));
    check_catalogue(&ir);
}
