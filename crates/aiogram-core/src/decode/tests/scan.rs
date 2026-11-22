//! The structural scanner of the failure paths.

use crate::decode::scan::{update_id, value_end};

fn end(json: &str) -> Option<usize> {
    value_end(json.as_bytes(), 0)
}

#[test]
fn value_end_follows_structure_only() {
    assert_eq!(end(r#"{"a":"}]","b":[1,{"c":"\"{"}]} tail"#), Some(30));
    assert_eq!(end(r#"  "x\\" ,"#), Some(7));
    assert_eq!(end("-12.5e3,"), Some(7));
    assert_eq!(end("true}"), Some(4));
    assert_eq!(end("null"), Some(4));
    // escapes are not validated: a lone surrogate passes
    assert_eq!(end(r#"{"a":"\ud800"}"#), Some(14));
    // no nesting limit
    let deep = format!("{}{}", "[".repeat(100_000), "]".repeat(100_000));
    assert_eq!(end(&deep), Some(200_000));
}

#[test]
fn value_end_rejects_what_does_not_balance() {
    assert_eq!(end(r#"{"a":[1,2}"#), None);
    assert_eq!(end(r#"{"a":"open"#), None);
    assert_eq!(end(r#""\"#), None);
    assert_eq!(end("}"), None);
    assert_eq!(end(""), None);
    assert_eq!(end("   "), None);
    assert_eq!(end(","), None);
}

#[test]
fn update_id_is_read_by_a_shallow_scan() {
    let id = |json: &str| update_id(json.as_bytes());
    assert_eq!(id(r#"{"update_id":7,"message":{}}"#), Some(7));
    assert_eq!(
        id(r#" { "message" : {"x":"\ud800"} , "update_id" : -3 } "#),
        Some(-3)
    );
    let deep = format!(
        r#"{{"message":{}1{},"update_id":9}}"#,
        "[".repeat(10_000),
        "]".repeat(10_000)
    );
    assert_eq!(id(&deep), Some(9));
    assert_eq!(id(r#"{"message":{}}"#), None);
    assert_eq!(id(r#"{"update_id":"7"}"#), None);
    assert_eq!(id(r#"{"update_id":1e3}"#), None);
    assert_eq!(id(r#"{"update_id":99999999999999999999}"#), None);
    assert_eq!(id(r#"[{"update_id":1}]"#), None);
    assert_eq!(id(r#"{"message":{]},"update_id":1}"#), None);
    assert_eq!(id(r#"{"message" 1,"update_id":1}"#), None);
    assert_eq!(id(r#"{"a":1 "update_id":1}"#), None);
    assert_eq!(id(r#"{}"#), None);
}

// ---- review fixes ----

#[test]
fn mismatched_brackets_do_not_balance() {
    assert_eq!(end(r#"{"a":[}"#), None);
    assert_eq!(end(r#"[{"a":1]}"#), None);
    assert_eq!(end(r#"{"x":[},{"update_id":2}]"#), None);
}

#[test]
fn duplicate_update_id_last_wins() {
    let id = |json: &str| update_id(json.as_bytes());
    assert_eq!(
        id(r#"{"update_id":100,"message":{},"update_id":2}"#),
        Some(2)
    );
    assert_eq!(id(r#"{"update_id":"x","update_id":3}"#), Some(3));
    assert_eq!(id(r#"{"update_id":3,"update_id":"x"}"#), None);
}
