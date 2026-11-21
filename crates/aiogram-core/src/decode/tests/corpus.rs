//! Acceptance on the A-04 corpus (`benchmarks/corpus/MANIFEST.toml`, path `wire/<id>.json`).

use jiter::Jiter;

use super::types::{Message, MessageCold, Update, m};
use crate::decode::{ColdField, Decode, Meta, Raw, Table};

fn corpus(id: &str) -> Vec<u8> {
    let path = format!(
        "{}/../../benchmarks/corpus/wire/{id}.json",
        env!("CARGO_MANIFEST_DIR")
    );
    std::fs::read(&path).unwrap_or_else(|e| panic!("{path}: {e}"))
}

/// The keys of the JSON object at `span`, in input order.
fn json_keys(buf: &[u8], span: Raw) -> Vec<String> {
    let mut jiter = Jiter::new(span.slice(buf).unwrap());
    let mut keys = Vec::new();
    let mut key = jiter.next_object().unwrap().map(str::to_owned);
    while let Some(k) = key {
        keys.push(k);
        jiter.next_skip().unwrap();
        key = jiter.next_key().unwrap().map(str::to_owned);
    }
    keys
}

/// Every key of the object is either a set field or an unknown key, and nothing else: the
/// decoded field set equals the input's key set (B-04's debug walk, on one object).
fn assert_accounted<B: AsRef<[u64]>>(buf: &[u8], table: &Table, meta: &Meta<B>) -> Vec<String> {
    let mut input = json_keys(buf, meta.span);
    input.sort();
    let unknown: Vec<String> = meta
        .unknown
        .iter()
        .map(|u| String::from_utf8(u.key.slice(buf).unwrap().to_vec()).unwrap())
        .collect();
    let mut seen: Vec<String> = (0..table.fields.len())
        .map(|id| u16::try_from(id).unwrap())
        .filter(|id| meta.is_set(*id))
        .map(|id| table.wire(id).to_owned())
        .chain(unknown.iter().cloned())
        .collect();
    seen.sort();
    assert_eq!(seen, input);
    unknown
}

#[test]
fn update_realistic() {
    let buf = corpus("update.realistic");
    let update = Update::from_slice(&buf, 0).unwrap();
    // the file's trailing newline is outside the object
    let end = u32::try_from(buf.trim_ascii_end().len()).unwrap();
    assert_eq!(update.meta.span, Raw { start: 0, end });
    assert!(assert_accounted(&buf, Update::TABLE, &update.meta).is_empty());

    let msg = update.message.as_deref().unwrap();
    assert!(assert_accounted(&buf, Message::TABLE, &msg.meta).is_empty());
    // every hot field of the fixture is inline
    assert!(msg.message_thread_id.is_some() && msg.caption.is_some() && msg.reply_markup.is_some());
    assert_eq!(msg.photo.as_deref().unwrap().len(), 4);
    assert_eq!(msg.caption_entities.as_deref().unwrap().len(), 6);
    let keyboard = &msg.reply_markup.as_ref().unwrap().inline_keyboard;
    assert_eq!(
        keyboard.iter().map(|row| row.len()).collect::<Vec<_>>(),
        [2, 2, 2]
    );
    // the fixture's cold fields are in the sorted vec, decoded (not opaque)
    let cold: Vec<u16> = msg.cold.iter().map(ColdField::id).collect();
    assert_eq!(cold, [m::IS_TOPIC_MESSAGE, m::QUOTE]);
    let Some(MessageCold::Quote(quote)) = msg.cold(m::QUOTE) else {
        panic!()
    };
    assert!(assert_accounted(&buf, &super::types::TEXT_QUOTE, &quote.meta).is_empty());

    // keys the reduced test tables leave out are raw ranges into the buffer
    let from = msg.from_user.as_ref().unwrap();
    assert_eq!(
        assert_accounted(&buf, &super::types::USER, &from.meta),
        ["last_name"]
    );
    assert_eq!(
        from.meta.unknown[0].value.slice(&buf).unwrap(),
        br#""Example""#
    );
    for photo in msg.photo.as_deref().unwrap() {
        assert_eq!(
            assert_accounted(&buf, &super::types::PHOTO_SIZE, &photo.meta),
            ["file_size"]
        );
    }
    let reply = msg.reply_to_message.as_deref().unwrap();
    assert!(assert_accounted(&buf, Message::TABLE, &reply.meta).is_empty());
    assert!(reply.text.is_some() && reply.entities.is_some());
    assert!(assert_accounted(&buf, &super::types::CHAT, &reply.chat.meta).is_empty());
}

#[test]
fn update_message_wide_sparse() {
    let buf = corpus("update.message.wide-sparse");
    let update = Update::from_slice(&buf, 0).unwrap();
    let msg = update.message.as_deref().unwrap();
    assert!(assert_accounted(&buf, Message::TABLE, &msg.meta).is_empty());
    let set: u32 = msg.meta.present.iter().map(|w| w.count_ones()).sum();
    assert_eq!(set, 29);
    // 6 hot fields inline, the other 23 in the sorted cold vec: 18 decoded, 5 opaque
    let ids: Vec<u16> = msg.cold.iter().map(ColdField::id).collect();
    assert_eq!(ids.len(), 23);
    assert!(ids.windows(2).all(|w| w[0] < w[1]));
    let opaque = msg
        .cold
        .iter()
        .filter(|f| matches!(f, MessageCold::Opaque(..)))
        .count();
    assert_eq!(opaque, 5);
    assert_eq!(msg.via_bot().unwrap().id, 900_000_001);
    assert!(msg.edit_date().is_some());
    let animation = msg.opaque(m::ANIMATION).unwrap();
    assert!(
        animation
            .slice(&buf)
            .unwrap()
            .starts_with(br#"{"file_id":"#)
    );
}
