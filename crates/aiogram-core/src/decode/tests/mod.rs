//! `cargo test` of the decode core, no interpreter (except the one `PyErr` mapping test).

mod corpus;
mod types;

use pyo3::prelude::*;

use super::{
    Cursor, Decode, DecodeError, ErrorKind, INTERNED, IStr, Kind, Raw, Table, UnixTime, bit,
};
use types::{
    CHAT, ChatType, EntityType, INLINE_KEYBOARD_BUTTON, INLINE_KEYBOARD_MARKUP, LOCATION, MESSAGE,
    MESSAGE_ENTITY, Message, MessageCold, PHOTO_SIZE, TEXT_QUOTE, UPDATE, USER, Update, User, m,
};

fn text(buf: &[u8], raw: Raw) -> &str {
    std::str::from_utf8(raw.slice(buf).unwrap()).unwrap()
}

fn update(json: &str) -> Update {
    Update::from_slice(json.as_bytes(), 0).unwrap()
}

fn error(json: &str) -> DecodeError {
    Update::from_slice(json.as_bytes(), 0).unwrap_err()
}

fn message(json: &str) -> Message {
    Message::from_slice(json.as_bytes(), 0).unwrap()
}

const CHAT_JSON: &str = r#"{"id":-100,"type":"supergroup","title":"T"}"#;

fn wrap(fields: &str) -> String {
    format!(r#"{{"message_id":1,"date":1700000000,"chat":{CHAT_JSON}{fields}}}"#)
}

// ---- tables ----

fn check_table(name: &str, table: &Table, width: usize) {
    assert!(
        table.fields.len() <= width * 64,
        "{name}: present bitset too narrow"
    );
    assert!(
        table.keys.windows(2).all(|w| w[0].0 < w[1].0),
        "{name}: keys not sorted or duplicated"
    );
    for (id, field) in table.fields.iter().enumerate() {
        let id = u16::try_from(id).unwrap();
        assert_eq!(
            table.lookup(field.wire.as_bytes()),
            Some(id),
            "{name}.{}",
            field.wire
        );
        assert!(
            !(field.required && field.cold),
            "{name}.{}: required and cold",
            field.wire
        );
        assert!(
            field.kind != Kind::Opaque || field.cold,
            "{name}.{}: hot opaque",
            field.wire
        );
    }
    for (key, id) in table.keys {
        assert!(
            usize::from(*id) < table.fields.len(),
            "{name}: key {key} out of range"
        );
    }
}

#[test]
fn tables_are_consistent() {
    for (name, table, width) in [
        ("User", &USER, 1),
        ("Chat", &CHAT, 1),
        ("MessageEntity", &MESSAGE_ENTITY, 1),
        ("PhotoSize", &PHOTO_SIZE, 1),
        ("TextQuote", &TEXT_QUOTE, 1),
        ("Location", &LOCATION, 1),
        ("InlineKeyboardButton", &INLINE_KEYBOARD_BUTTON, 1),
        ("InlineKeyboardMarkup", &INLINE_KEYBOARD_MARKUP, 1),
        ("Message", &MESSAGE, 3),
        ("Update", &UPDATE, 1),
    ] {
        check_table(name, table, width);
    }
    assert_eq!(MESSAGE.fields.len(), 130);
    assert!(INTERNED.windows(2).all(|w| w[0] < w[1]));
}

// ---- value kinds ----

#[test]
fn value_kinds() {
    let json = wrap(
        r#","text":"a\"é😀","from":{"id":5,"is_bot":false,"first_name":"A","language_code":"uk"},
        "entities":[{"type":"bold","offset":0,"length":-2147483648},{"type":"spoiler","offset":1,"length":2}],
        "location":{"latitude":50,"longitude":30.5,"horizontal_accuracy":1e2},
        "is_topic_message":true,"edit_date":1700000001,
        "reply_markup":{"inline_keyboard":[[{"text":"x","callback_data":"d"}],[]]},
        "sticker":{"any": [1, {"nested": null}]}"#,
    );
    let msg = message(&json);
    assert_eq!(msg.message_id, 1);
    assert_eq!(msg.date, UnixTime(1_700_000_000));
    assert_eq!(msg.chat.id, -100);
    assert_eq!(msg.chat.kind, ChatType::Supergroup);
    assert_eq!(msg.text.as_deref(), Some("a\"\u{e9}\u{1f600}"));
    let user = msg.from_user.as_ref().unwrap();
    assert_eq!(user.language_code, Some(IStr::Known("uk")));
    assert!(user.cold.is_none());
    let entities = msg.entities.as_deref().unwrap();
    assert_eq!(entities[0].kind, EntityType::Bold);
    assert_eq!(entities[0].length, i32::MIN);
    assert_eq!(entities[1].kind, EntityType::Unknown("spoiler".into()));
    let Some(MessageCold::Location(location)) = msg.cold(m::LOCATION) else {
        panic!()
    };
    assert_eq!((location.latitude, location.longitude), (50.0, 30.5));
    assert_eq!(location.horizontal_accuracy, Some(100.0));
    assert!(matches!(
        msg.cold(m::IS_TOPIC_MESSAGE),
        Some(MessageCold::IsTopicMessage(true))
    ));
    assert_eq!(msg.edit_date(), Some(UnixTime(1_700_000_001)));
    let keyboard = &msg.reply_markup.as_ref().unwrap().inline_keyboard;
    assert_eq!(keyboard.len(), 2);
    assert_eq!(&*keyboard[0][0].text, "x");
    assert_eq!(keyboard[0][0].callback_data.as_deref(), Some("d"));
    assert!(keyboard[1].is_empty());
    let sticker = msg.opaque(m::STICKER).unwrap();
    assert_eq!(
        text(json.as_bytes(), sticker),
        r#"{"any": [1, {"nested": null}]}"#
    );
}

#[test]
fn istr_owned_when_not_interned() {
    assert_eq!(IStr::new("xx-yy"), IStr::Owned("xx-yy".into()));
    assert_eq!(IStr::new("en").as_str(), "en");
    assert!(matches!(IStr::new("en"), IStr::Known(s) if std::ptr::eq(s, INTERNED[4])));
}

#[test]
fn integer_errors() {
    let e = error(&format!(
        r#"{{"update_id":1,"message":{}}}"#,
        wrap(r#","entities":[{"type":"bold","offset":2147483648,"length":1}]"#)
    ));
    assert_eq!(e.path(), "message.entities[0].offset");
    assert_eq!(*e.kind(), ErrorKind::Range("i32"));

    let e = error(r#"{"update_id":99999999999999999999}"#);
    assert_eq!(
        (e.path().as_str(), e.kind()),
        ("update_id", &ErrorKind::Range("i64"))
    );
    assert_eq!(e.offset(), 13);

    let e = error(r#"{"update_id":1.5}"#);
    assert_eq!(e.path(), "update_id");
    assert!(matches!(e.kind(), ErrorKind::Json(_)));

    let e = error(r#"{"update_id":"1"}"#);
    assert!(
        matches!(e.kind(), ErrorKind::Json(m) if m.contains("int")),
        "{e}"
    );
}

#[test]
fn wrong_type_for_object_and_array() {
    let e = error(r#"{"update_id":1,"message":"x"}"#);
    assert_eq!(e.path(), "message");
    let e = Message::from_slice(wrap(r#","photo":{}"#).as_bytes(), 0).unwrap_err();
    assert_eq!(e.path(), "photo");
}

// ---- unknown keys, present bits, sparse layout ----

#[test]
fn unknown_keys_are_raw_ranges() {
    let json = r#"{"update_id":7, "callback_query" : {"id":"q","x":[1,2]},"message":{"message_id":1,"date":2,"chat":{"id":3,"type":"private"},"from":{"id":5,"is_bot":true,"first_name":"B","last_name":"L"}},"zz":null}"#;
    let upd = update(json);
    let buf = json.as_bytes();
    let unknown: Vec<_> = upd
        .meta
        .unknown
        .iter()
        .map(|u| (text(buf, u.key), text(buf, u.value)))
        .collect();
    assert_eq!(
        unknown,
        [
            ("callback_query", r#"{"id":"q","x":[1,2]}"#),
            ("zz", "null")
        ]
    );
    let user = upd.message.as_ref().unwrap().from_user.as_ref().unwrap();
    assert_eq!(text(buf, user.meta.unknown[0].key), "last_name");
    assert_eq!(text(buf, user.meta.unknown[0].value), r#""L""#);
    // the object's own span
    assert_eq!(text(buf, upd.meta.span), json);
    assert!(text(buf, user.meta.span).starts_with(r#"{"id":5"#));
    // no unknown keys, no allocation
    assert!(upd.message.as_ref().unwrap().meta.unknown.is_empty());
}

#[test]
fn lone_surrogates() {
    // in a decoded string: an error at the field (Rust `str` cannot hold it)
    let e = Message::from_slice(wrap(r#","text":"\ud800""#).as_bytes(), 0).unwrap_err();
    assert_eq!(e.path(), "text");
    // jiter: "unexpected end of hex escape" (`\ud800"`) or "lone leading surrogate" (`\udc00`)
    assert!(
        matches!(e.kind(), ErrorKind::Json(m) if m.contains("hex escape")),
        "{e}"
    );
    // jiter checks escapes in skipped values too: an unknown key's value or an opaque field
    // fails at the enclosing known field, with the offset of the escape
    for (fields, path, escape) in [
        (r#","x":"\ud800""#, "message", r"\ud800"),
        (
            r#","sticker":{"emoji":"\udc00"}"#,
            "message.sticker",
            r"\udc00",
        ),
    ] {
        let json = format!(r#"{{"update_id":1,"message":{}}}"#, wrap(fields));
        let e = error(&json);
        assert_eq!(e.path(), path, "{e}");
        let at = json.find(escape).unwrap();
        let offset = e.offset() as usize;
        assert!(
            (at..=at + escape.len() + 1).contains(&offset),
            "{e} vs {at}"
        );
    }
    // a valid pair is fine everywhere
    let msg = message(&wrap(r#","x":"\ud83d\ude00","text":"\ud83d\ude00""#));
    assert_eq!(msg.text.as_deref(), Some("\u{1f600}"));
}

#[test]
fn present_bits() {
    let msg = message(&wrap(
        r#","text":null,"reply_markup":{"inline_keyboard":[]},"ton_wallet_transfer":{},"nope":1"#,
    ));
    let present = &msg.meta.present;
    for id in [
        m::MESSAGE_ID,
        m::DATE,
        m::CHAT,
        m::TEXT,
        m::REPLY_MARKUP,
        m::TON_WALLET_TRANSFER,
    ] {
        assert!(msg.meta.is_set(id), "{id}");
    }
    // `null` is set, its value None (exclude_unset keeps it, as pydantic does)
    assert!(msg.text.is_none());
    // reply_markup (113) and ton_wallet_transfer (122) are in the second word
    assert!(present[1] != 0 && present[2] == 0);
    assert_eq!(present.iter().map(|w| w.count_ones()).sum::<u32>(), 6);
    assert!(!bit(present, m::CAPTION));
    assert!(!bit(present, 999));
}

#[test]
fn boxed_cold_struct() {
    let json = r#"{"id":1,"is_bot":false,"first_name":"A","is_premium":true}"#;
    let user = User::from_slice(json.as_bytes(), 0).unwrap();
    let cold = user.cold.as_ref().unwrap();
    assert_eq!(
        (cold.is_premium, cold.added_to_attachment_menu),
        (Some(true), None)
    );
    let chat = types::Chat::from_slice(CHAT_JSON.as_bytes(), 0).unwrap();
    assert!(chat.cold.is_none());
}

#[test]
fn sorted_cold_vec() {
    // input order differs from id order; one cold field repeated, one set then cleared by null
    let json = wrap(
        r#","edit_date":5,"via_bot":{"id":9,"is_bot":true,"first_name":"Bot"},"paid_star_count":3,
        "forward_date":1,"sender_tag":"t","edit_date":6,"paid_star_count":null,"giveaway":[]"#,
    );
    let msg = message(&json);
    let ids: Vec<u16> = msg.cold.iter().map(super::ColdField::id).collect();
    assert_eq!(
        ids,
        [
            m::SENDER_TAG,
            m::VIA_BOT,
            m::EDIT_DATE,
            m::GIVEAWAY,
            m::FORWARD_DATE
        ]
    );
    assert_eq!(msg.edit_date(), Some(UnixTime(6)));
    assert_eq!(msg.via_bot().unwrap().id, 9);
    assert!(msg.cold(m::PAID_STAR_COUNT).is_none());
    assert!(msg.meta.is_set(m::PAID_STAR_COUNT));
    assert_eq!(
        text(json.as_bytes(), msg.opaque(m::FORWARD_DATE).unwrap()),
        "1"
    );
    // an all-hot message has an empty cold vec, no allocation
    assert!(message(&wrap("")).cold.is_empty());
}

// ---- input rules ----

#[test]
fn duplicate_keys_last_wins() {
    let msg = message(&wrap(r#","text":"a","text":"b","message_id":2"#));
    assert_eq!((msg.text.as_deref(), msg.message_id), (Some("b"), 2));
    // a required field set then nulled is missing
    let e = Message::from_slice(wrap(r#","message_id":null"#).as_bytes(), 0).unwrap_err();
    assert_eq!(
        (e.path().as_str(), e.kind()),
        ("message_id", &ErrorKind::Missing)
    );
}

#[test]
fn python_alias_is_the_same_field() {
    let user = r#"{"id":1,"is_bot":false,"first_name":"A"}"#;
    let user2 = r#"{"id":2,"is_bot":false,"first_name":"B"}"#;
    let msg = message(&wrap(&format!(r#","from_user":{user}"#)));
    assert_eq!(msg.from_user.as_ref().unwrap().id, 1);
    assert!(msg.meta.unknown.is_empty() && msg.meta.is_set(m::FROM));
    let msg = message(&wrap(&format!(r#","from_user":{user},"from":{user2}"#)));
    assert_eq!(msg.from_user.as_ref().unwrap().id, 2);
    let msg = message(&wrap(&format!(r#","from":{user2},"from_user":{user}"#)));
    assert_eq!(msg.from_user.as_ref().unwrap().id, 1);
    // errors name the wire field
    let e = Message::from_slice(wrap(r#","from_user":{"id":1}"#).as_bytes(), 0).unwrap_err();
    assert_eq!(e.path(), "from.is_bot");
}

#[test]
fn escaped_keys_are_decoded() {
    let msg = message(&wrap(r#","text":"x""#));
    assert_eq!(msg.text.as_deref(), Some("x"));
    let e = Message::from_slice(wrap(r#","\udc00":1"#).as_bytes(), 0).unwrap_err();
    assert!(e.to_string().contains("surrogate"), "{e}");
}

// ---- errors ----

#[test]
fn missing_required_field_has_its_path() {
    let e = error(r#"{"update_id":1,"message":{"message_id":1,"date":2}}"#);
    assert_eq!(
        (e.path().as_str(), e.kind()),
        ("message.chat", &ErrorKind::Missing)
    );
    assert_eq!(e.offset(), 25);
    assert_eq!(
        e.to_string(),
        "message.chat: missing required field at byte 25"
    );

    let e = error(&format!(
        r#"{{"update_id":1,"message":{}}}"#,
        wrap(
            r#","reply_to_message":{"message_id":2,"date":3,"chat":{"id":1,"type":"private"},"entities":[{"type":"url","offset":0,"length":1},{"offset":0,"length":1}]}"#
        )
    ));
    assert_eq!(e.path(), "message.reply_to_message.entities[1].type");

    let e = error(r#"{}"#);
    assert_eq!((e.path().as_str(), e.offset()), ("update_id", 0));
}

#[test]
fn invalid_json() {
    for (json, offset) in [
        (r#"{"update_id":1"#, 14),
        (r#"{"update_id":1,}"#, 15),
        (r#"{"update_id":1} x"#, 16),
        (r#"[1]"#, 0),
        (r#"{"update_id":1,"x":[1,}"#, 22),
    ] {
        let e = error(json);
        assert!(matches!(e.kind(), ErrorKind::Json(_)), "{json}: {e}");
        assert_eq!(e.offset(), offset, "{json}: {e}");
    }
}

#[test]
fn sub_slice_decode_keeps_buffer_offsets() {
    // B-14 decodes a member on a fresh cursor over its slice; ranges stay update-relative
    let json =
        r#"{"update_id":1,"message":{"message_id":1,"date":2,"chat":{"id":3,"type":"x","q":1}}}"#;
    let whole = update(json);
    let chat = &whole.message.as_ref().unwrap().chat;
    let start = chat.meta.span.start;
    let slice = chat.meta.span.slice(json.as_bytes()).unwrap();
    let again = types::Chat::from_slice(slice, start).unwrap();
    assert_eq!(again.meta, chat.meta);
    assert_eq!(again.kind, ChatType::Unknown("x".into()));
    assert_eq!(text(json.as_bytes(), again.meta.unknown[0].key), "q");
    // errors too
    let e = types::Chat::from_slice(br#"{"id":"x"}"#, 1000).unwrap_err();
    assert_eq!(e.offset(), 1006);
}

#[test]
fn buffer_past_u32_is_rejected() {
    let e = Cursor::new(b"{}", u32::MAX - 1).err().unwrap();
    assert_eq!(*e.kind(), ErrorKind::TooLarge);
    assert!(Cursor::new(b"{}", u32::MAX - 2).is_ok());
}

#[test]
fn error_maps_to_value_error() {
    Python::initialize();
    Python::attach(|py| {
        let err: PyErr = error("{}").into();
        assert!(err.is_instance_of::<pyo3::exceptions::PyValueError>(py));
        assert_eq!(
            err.value(py).to_string(),
            "update_id: missing required field at byte 0"
        );
    });
}
