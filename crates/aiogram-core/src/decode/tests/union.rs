//! Unions (10 Layer 1, D107) and the `Unknown…` hook.

use super::corpus::corpus;
use super::types::{ChatMember, MaybeInaccessibleMessage, Message, MessageOrigin, Update};
use super::wrap;
use crate::decode::seen::{self, Counter, MAX_KEYS, Seen};
use crate::decode::{Cursor, Decode, ErrorKind, Raw, Site};

fn text(buf: &[u8], raw: Raw) -> &str {
    std::str::from_utf8(raw.slice(buf).unwrap()).unwrap()
}

fn message(json: &str) -> Message {
    Message::from_slice(json.as_bytes(), 0).unwrap()
}

#[test]
fn unknown_tag_is_the_unknown_variant() {
    let buf = corpus("update.unknown-tag");
    let update = Update::from_slice(&buf, 0).unwrap();
    let updated = update.chat_member.as_deref().unwrap();
    let ChatMember::Member(old) = &updated.old_chat_member else {
        panic!("{:?}", updated.old_chat_member)
    };
    assert_eq!(old.user.id, 100_000_002);
    let ChatMember::Unknown(unknown) = &updated.new_chat_member else {
        panic!("{:?}", updated.new_chat_member)
    };
    assert_eq!(unknown.tag.as_deref(), Some("superadmin"));
    assert_eq!(
        unknown.common.as_ref().unwrap().user.first_name.as_ref(),
        "Bob"
    );
    assert!(unknown.error.is_none());
    assert!(text(&buf, unknown.raw).starts_with(r#"{"status":"superadmin","user":"#));
    assert!(text(&buf, unknown.raw).ends_with(r#""username":"bob_example"}}"#));
}

#[test]
fn malformed_member_is_absorbed() {
    let buf = corpus("update.malformed-member");
    let update = Update::from_slice(&buf, 0).unwrap();
    let msg = update.message.as_deref().unwrap();
    assert_eq!(msg.text.as_deref(), Some("forwarded"));
    let Some(MessageOrigin::Unknown(unknown)) = msg.forward_origin() else {
        panic!("{:?}", msg.forward_origin())
    };
    assert_eq!(unknown.tag.as_deref(), Some("user"));
    assert_eq!(unknown.common.as_ref().unwrap().date.0, 1_763_424_000);
    let error = unknown.error.as_ref().unwrap();
    assert_eq!(error.kind(), &ErrorKind::Missing);
    assert_eq!(error.path(), "sender_user");
    assert_eq!(
        text(&buf, unknown.raw),
        r#"{"type":"user","date":1763424000}"#
    );
}

#[test]
fn known_variants_decode() {
    let msg = message(&wrap(
        r#","forward_origin":{"date":5,"sender_user_name":"Anon","type":"hidden_user"}"#,
    ));
    let Some(MessageOrigin::HiddenUser(origin)) = msg.forward_origin() else {
        panic!("{:?}", msg.forward_origin())
    };
    assert_eq!(
        (origin.date.0, origin.sender_user_name.as_ref()),
        (5, "Anon")
    );

    let json = r#"{"status":"administrator","user":{"id":1,"is_bot":false,"first_name":"A"},"can_be_edited":true}"#;
    let mut c = Cursor::new(json.as_bytes(), 0).unwrap();
    let ChatMember::Administrator(admin) =
        <ChatMember as crate::decode::Union>::decode(&mut c).unwrap()
    else {
        panic!()
    };
    assert!(admin.can_be_edited);
    c.finish().unwrap();
}

#[test]
fn predicate_union() {
    let msg = message(&wrap(&format!(
        r#","pinned_message":{}"#,
        wrap(r#","text":"p""#)
    )));
    let Some(MaybeInaccessibleMessage::Message(pinned)) = msg.pinned_message() else {
        panic!("{:?}", msg.pinned_message())
    };
    assert_eq!(pinned.text.as_deref(), Some("p"));

    let msg = message(&wrap(
        r#","pinned_message":{"chat":{"id":1,"type":"private"},"message_id":9,"date":0}"#,
    ));
    let Some(MaybeInaccessibleMessage::Inaccessible(gone)) = msg.pinned_message() else {
        panic!("{:?}", msg.pinned_message())
    };
    assert_eq!((gone.message_id, gone.date.0), (9, 0));

    // no `date`: Message is selected and misses it; the shared fields miss it too
    let msg = message(&wrap(
        r#","pinned_message":{"chat":{"id":1,"type":"private"},"message_id":9},"text":"after""#,
    ));
    let Some(MaybeInaccessibleMessage::Unknown(unknown)) = msg.pinned_message() else {
        panic!("{:?}", msg.pinned_message())
    };
    assert!(unknown.tag.is_none() && unknown.common.is_none());
    assert_eq!(unknown.error.as_ref().unwrap().path(), "date");
    assert_eq!(msg.text.as_deref(), Some("after"));
}

#[test]
fn absorbed_member_leaves_the_rest_of_the_object() {
    let json = wrap(
        r#","forward_origin":{"type":"user","date":1,"sender_user":5,"extra":[1,{"a":"}"}]},"text":"after""#,
    );
    let msg = message(&json);
    assert_eq!(msg.text.as_deref(), Some("after"));
    let Some(MessageOrigin::Unknown(unknown)) = msg.forward_origin() else {
        panic!("{:?}", msg.forward_origin())
    };
    assert_eq!(unknown.error.as_ref().unwrap().path(), "sender_user");
    assert!(text(json.as_bytes(), unknown.raw).ends_with(r#"{"a":"}"}]}"#));
}

#[test]
fn lone_surrogate_in_a_member_is_absorbed() {
    let json = wrap(
        r#","forward_origin":{"type":"hidden_user","date":1,"sender_user_name":"\ud800"},"text":"after""#,
    );
    let msg = message(&json);
    assert_eq!(msg.text.as_deref(), Some("after"));
    let Some(MessageOrigin::Unknown(unknown)) = msg.forward_origin() else {
        panic!("{:?}", msg.forward_origin())
    };
    assert!(matches!(
        unknown.error.as_ref().unwrap().kind(),
        ErrorKind::Json(_)
    ));
    // the shared fields precede the bad string, but jiter rejects it in skipped values too
    assert!(unknown.common.is_none());
}

#[test]
fn member_of_the_wrong_type_is_absorbed() {
    let json = wrap(r#","forward_origin":[1,2],"text":"after""#);
    let msg = message(&json);
    assert_eq!(msg.text.as_deref(), Some("after"));
    let Some(MessageOrigin::Unknown(unknown)) = msg.forward_origin() else {
        panic!("{:?}", msg.forward_origin())
    };
    assert!(unknown.tag.is_none() && unknown.common.is_none());
    assert!(unknown.error.is_some());
    assert_eq!(text(json.as_bytes(), unknown.raw), "[1,2]");
}

#[test]
fn escaped_tag_is_an_unknown_tag() {
    // `"\u0075ser"`, built here: the escape is the point of the test
    let tag = format!("{}u0075ser", '\\');
    let msg = message(&wrap(&format!(
        r#","forward_origin":{{"type":"{tag}","date":1}}"#
    )));
    let Some(MessageOrigin::Unknown(unknown)) = msg.forward_origin() else {
        panic!("{:?}", msg.forward_origin())
    };
    assert_eq!(unknown.tag.as_deref(), Some("user"));
    assert!(unknown.error.is_none(), "{:?}", unknown.error);
}

#[test]
fn unbalanced_member_fails_the_object() {
    let json = wrap(r#","forward_origin":{"type":"user","date":1,"sender_user":{"id":1]"#);
    assert!(Message::from_slice(json.as_bytes(), 0).is_err());
    let json = wrap(r#","forward_origin":{"type":"new","date":1,"x":[}"#);
    let error = Message::from_slice(json.as_bytes(), 0).unwrap_err();
    assert!(matches!(error.kind(), ErrorKind::Json(_)), "{error}");
}

// ---- the `Unknown…` hook ----

fn chat_member_update(status: &str) -> String {
    format!(
        r#"{{"update_id":1,"chat_member":{{"chat":{{"id":1,"type":"group"}},"from":{{"id":1,"is_bot":false,"first_name":"A"}},"date":1,"old_chat_member":{{"status":"member","user":{{"id":2,"is_bot":false,"first_name":"B"}}}},"new_chat_member":{{"status":"{status}","user":{{"id":2,"is_bot":false,"first_name":"B"}}}}}}}}"#
    )
}

fn decode(json: &str, strict: bool) -> (crate::decode::DecodeResult<Update>, Vec<Seen>) {
    let mut c = Cursor::new(json.as_bytes(), 0).unwrap().strict(strict);
    let out = Update::decode(&mut c);
    (out, c.take_seen())
}

fn count(seen: &Seen) -> u64 {
    seen::snapshot()
        .0
        .into_iter()
        .find(|(key, _)| key == seen)
        .map_or(0, |(_, count)| count)
}

#[test]
fn hook_counts_once_and_strict_turns_it_into_an_error() {
    // values unique to this test: the counter is process-wide
    let json = chat_member_update("hooktest-once");
    let key = Seen::new("ChatMember", Site::Tag, "hooktest-once");

    let (first, seen) = decode(&json, false);
    assert!(first.is_ok());
    assert_eq!(seen, std::slice::from_ref(&key));
    let (second, seen) = decode(&json, false);
    assert!(second.is_ok());
    assert!(seen.is_empty(), "reported once");
    assert_eq!(count(&key), 2);

    let (strict, _) = decode(&json, true);
    let error = strict.unwrap_err();
    assert_eq!(error.kind(), &ErrorKind::Strict(Box::new(key.clone())));
    assert_eq!(error.path(), "chat_member.new_chat_member");
    assert_eq!(count(&key), 3);
    // a known tag is not an `Unknown`: strict mode decodes it
    assert!(decode(&chat_member_update("member"), true).0.is_ok());
}

#[test]
fn hook_sites() {
    let malformed = wrap(r#","forward_origin":{"type":"hooktest-user","date":"x"}"#);
    let mut c = Cursor::new(malformed.as_bytes(), 0).unwrap();
    Message::decode(&mut c).unwrap();
    assert_eq!(
        c.take_seen(),
        [Seen::new("MessageOrigin", Site::Tag, "hooktest-user")]
    );

    let malformed = wrap(r#","forward_origin":{"type":"user","date":"hooktest"}"#);
    let mut c = Cursor::new(malformed.as_bytes(), 0).unwrap().strict(true);
    let error = Message::decode(&mut c).unwrap_err();
    assert!(
        matches!(error.kind(), ErrorKind::Strict(seen) if seen.site == Site::Malformed),
        "{error}"
    );

    let json = r#"{"update_id":1,"hooktest_update":{},"message":{"message_id":1,"date":1,"chat":{"id":1,"type":"hooktest-chat"}}}"#;
    let (update, seen) = decode(json, false);
    assert!(update.is_ok());
    assert_eq!(
        seen,
        [
            Seen::new("ChatType", Site::Enum, "hooktest-chat"),
            Seen::new("Update", Site::UpdateType, "hooktest_update"),
        ]
    );
    let error = decode(json, true).0.unwrap_err();
    assert_eq!(error.path(), "message.chat.type");
}

#[test]
fn counter_is_bounded() {
    let mut counter = Counter::default();
    let key = |i: usize| Seen::new("T", Site::Tag, &i.to_string());
    for i in 0..MAX_KEYS {
        assert!(counter.record(&key(i)));
    }
    assert!(!counter.record(&key(MAX_KEYS)), "past the cap: never first");
    assert_eq!((counter.count(&key(MAX_KEYS)), counter.overflow()), (0, 1));
    assert!(!counter.record(&key(0)));
    assert_eq!(counter.count(&key(0)), 2);

    let long = Seen::new("T", Site::Tag, &"é".repeat(40));
    assert_eq!(long.value.len(), 64);
    assert_eq!(
        Seen::new("T", Site::Tag, &format!("a{}", "é".repeat(40)))
            .value
            .len(),
        63
    );
}

// ---- review fixes ----

#[test]
fn duplicate_selecting_key_last_wins() {
    let msg = message(&wrap(
        r#","forward_origin":{"type":"user","type":"hidden_user","date":1,"sender_user_name":"a"}"#,
    ));
    assert!(
        matches!(msg.forward_origin(), Some(MessageOrigin::HiddenUser(_))),
        "{:?}",
        msg.forward_origin()
    );
    let msg = message(&wrap(
        r#","pinned_message":{"chat":{"id":1,"type":"private"},"message_id":9,"date":0,"date":5}"#,
    ));
    let Some(MaybeInaccessibleMessage::Message(pinned)) = msg.pinned_message() else {
        panic!("{:?}", msg.pinned_message())
    };
    assert_eq!(pinned.date.0, 5);
}

#[test]
fn escaped_selecting_key_is_decoded() {
    // `"type"`, built here: the escape is the point of the test
    let key = format!("ty{}u0070e", '\\');
    let msg = message(&wrap(&format!(
        r#","forward_origin":{{"{key}":"hidden_user","date":1,"sender_user_name":"a"}}"#
    )));
    assert!(
        matches!(msg.forward_origin(), Some(MessageOrigin::HiddenUser(_))),
        "{:?}",
        msg.forward_origin()
    );
}

#[test]
fn member_without_a_tag_is_malformed() {
    for member in ["[1,2]", r#"{"date":1}"#] {
        let json = wrap(&format!(r#","forward_origin":{member}"#));
        let mut c = Cursor::new(json.as_bytes(), 0).unwrap().strict(true);
        let error = Message::decode(&mut c).unwrap_err();
        assert!(
            matches!(error.kind(), ErrorKind::Strict(seen) if seen.site == Site::Malformed),
            "{member}: {error}"
        );
    }
}
