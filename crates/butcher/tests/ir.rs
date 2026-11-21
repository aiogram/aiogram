// clippy.toml's allow-*-in-tests covers #[test] fns only, not the helpers of an integration test crate
#![allow(clippy::unwrap_used)]

use std::path::{Path, PathBuf};

use butcher::Error;
use butcher::ir::{Fact, Ir, Provenance};

const FIXTURE: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/ir.json");

fn tmp(name: &str) -> PathBuf {
    Path::new(env!("CARGO_TARGET_TMPDIR")).join(name)
}

fn load_str(name: &str, text: &str) -> Result<Ir, Error> {
    let path = tmp(name);
    std::fs::write(&path, text).unwrap();
    Ir::load(&path)
}

#[test]
fn round_trip_is_byte_identical() {
    let fixture = std::fs::read(FIXTURE).unwrap();
    let ir = Ir::load(Path::new(FIXTURE)).unwrap();
    assert_eq!(ir.to_json().unwrap().as_bytes(), fixture.as_slice());

    let (a, b) = (tmp("round-trip-a.json"), tmp("round-trip-b.json"));
    ir.write(&a).unwrap();
    Ir::load(&a).unwrap().write(&b).unwrap();
    assert_eq!(std::fs::read(&a).unwrap(), fixture);
    assert_eq!(std::fs::read(&b).unwrap(), fixture);
}

#[test]
fn unknown_key_fails_with_its_path() {
    let text = std::fs::read_to_string(FIXTURE).unwrap();
    let needle = "\"name\": \"caption\",";
    assert!(text.contains(needle));
    let text = text.replacen(needle, "\"name\": \"caption\", \"requird\": true,", 1);
    let err = load_str("unknown-field.json", &text)
        .unwrap_err()
        .to_string();
    assert!(
        err.contains(": types[1].fields[2].requird: unknown field `requird`"),
        "{err}"
    );
}

#[test]
fn unknown_key_inside_a_fact_fails_with_its_path() {
    let text = std::fs::read_to_string(FIXTURE).unwrap();
    let text = text.replacen("\"by\": {", "\"since\": 1, \"by\": {", 1);
    let err = load_str("unknown-fact-key.json", &text)
        .unwrap_err()
        .to_string();
    assert!(
        err.contains("types[0].fields[2].type.since: unknown field `since`"),
        "{err}"
    );
}

#[test]
fn trailing_content_fails() {
    let text = std::fs::read_to_string(FIXTURE).unwrap() + "{}";
    let err = load_str("trailing.json", &text).unwrap_err();
    assert!(
        matches!(err, Error::Parse { ref at, .. } if at == "."),
        "{err}"
    );
}

#[test]
fn missing_file_is_an_io_error() {
    let err = Ir::load(&tmp("does-not-exist.json")).unwrap_err();
    assert!(matches!(err, Error::Io { .. }), "{err}");
}

/// Calls `f` on the provenance of every `Fact` in the IR.
fn each_fact(ir: &mut Ir, f: &mut impl FnMut(&mut Provenance)) {
    fn opt<T>(fact: &mut Option<Fact<T>>, f: &mut impl FnMut(&mut Provenance)) {
        if let Some(fact) = fact {
            f(&mut fact.by);
        }
    }
    for t in &mut ir.types {
        f(&mut t.direction.by);
        for field in &mut t.fields {
            f(&mut field.ty.by);
            for usage in [&mut field.request, &mut field.response]
                .into_iter()
                .flatten()
            {
                f(&mut usage.required.by);
                opt(&mut usage.constant, f);
                opt(&mut usage.default, f);
            }
            opt(&mut field.values, f);
            field.constraints.iter_mut().for_each(|c| f(&mut c.by));
        }
    }
    for m in &mut ir.methods {
        f(&mut m.returns.by);
        for p in &mut m.params {
            f(&mut p.ty.by);
            f(&mut p.required.by);
            opt(&mut p.constant, f);
            opt(&mut p.default, f);
            opt(&mut p.values, f);
            p.constraints.iter_mut().for_each(|c| f(&mut c.by));
        }
    }
    for e in &mut ir.enums {
        f(&mut e.values.by);
    }
    for u in &mut ir.unions {
        f(&mut u.members.by);
        opt(&mut u.discriminator, f);
    }
}

fn every_fact_carries(by: Provenance, marker: &str) {
    let mut ir = Ir::load(Path::new(FIXTURE)).unwrap();
    let mut facts = 0;
    each_fact(&mut ir, &mut |p| {
        *p = by.clone();
        facts += 1;
    });
    let json = ir.to_json().unwrap();
    // every serialised Fact has exactly one `"value"` key: the walker above saw them all
    assert_eq!(json.matches("\"value\":").count(), facts);
    let expected = if by.is_explicit() { 0 } else { facts };
    assert_eq!(json.matches(marker).count(), expected, "{marker}");
    let name = format!("prov-{}.json", marker.len());
    assert_eq!(load_str(&name, &json).unwrap(), ir);
}

#[test]
fn every_fact_can_be_explicit() {
    every_fact_carries(Provenance::Explicit, "\"by\"");
}

#[test]
fn every_fact_can_be_heuristic() {
    every_fact_carries(
        Provenance::Heuristic("rule.x".into()),
        "\"heuristic\": \"rule.x\"",
    );
}

#[test]
fn every_fact_can_be_overlay() {
    let by = Provenance::Overlay {
        file: "names.toml".into(),
        key: "Message.from".into(),
    };
    every_fact_carries(by, "\"file\": \"names.toml\"");
}

#[test]
fn fixture_uses_every_provenance_kind() {
    let mut ir = Ir::load(Path::new(FIXTURE)).unwrap();
    let mut kinds = [0; 3];
    each_fact(&mut ir, &mut |p| {
        kinds[match p {
            Provenance::Explicit => 0,
            Provenance::Heuristic(_) => 1,
            Provenance::Overlay { .. } => 2,
        }] += 1;
    });
    assert!(kinds.iter().all(|&n| n > 0), "{kinds:?}");
}
