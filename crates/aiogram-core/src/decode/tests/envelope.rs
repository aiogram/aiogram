//! The response envelope, the `getUpdates` batch and per-update isolation (10 Layer 2, R04).

use std::sync::Arc;

use super::alloc::live;
use super::corpus::corpus;
use super::depth::chain;
use super::types::{ChatMember, Message, Update};
use crate::decode::scan::value_end;
use crate::decode::{
    ApiError, BodyError, BodyResult, Decode, Decoded, ErrorKind, Item, Options, Raw, Response,
    Seen, Site, UpdateError, decode_response, decode_update, decode_updates,
};

const LENIENT: Options = Options { strict: false };

fn text(buf: &[u8], raw: Raw) -> &str {
    std::str::from_utf8(raw.slice(buf).unwrap()).unwrap()
}

fn updates(body: &[u8]) -> Vec<Item<Update>> {
    match decode_updates::<Update>(body, LENIENT).unwrap().value {
        Response::Ok(items) => items.into_vec(),
        Response::Err(error) => panic!("{error:?}"),
    }
}

fn batch(elements: &[&[u8]]) -> Vec<u8> {
    let mut body = br#"{"ok":true,"result":["#.to_vec();
    for (i, element) in elements.iter().enumerate() {
        if i > 0 {
            body.extend_from_slice(b", ");
        }
        body.extend_from_slice(element);
    }
    body.extend_from_slice(b"]}");
    body
}

fn trimmed(id: &str) -> Vec<u8> {
    corpus(id).trim_ascii_end().to_vec()
}

#[test]
fn get_updates_100() {
    let body = corpus("response.getUpdates.100");
    let items = updates(&body);
    assert_eq!(items.len(), 100);
    for (i, item) in items.iter().enumerate() {
        let update = item.data.as_ref().unwrap();
        assert_eq!(update.update_id, 30_001 + i64::try_from(i).unwrap());
        // the element's own bytes, offsets restarting at 0
        assert_eq!(
            update.meta.span,
            Raw {
                start: 0,
                end: u32::try_from(item.raw.len()).unwrap()
            }
        );
        assert!(item.raw.starts_with(br#"{"update_id":"#) && item.raw.ends_with(b"}"));
        let start = body
            .windows(item.raw.len())
            .position(|w| w == &*item.raw)
            .unwrap();
        assert_eq!(value_end(&body, start), Some(start + item.raw.len()));
    }
    let msg = items[0].data.as_ref().unwrap().message.as_deref().unwrap();
    assert_eq!(text(&items[0].raw, msg.chat.meta.span).len(), 103);
}

#[test]
fn missing_required_field_is_isolated_with_its_update_id() {
    let body = corpus("response.getUpdates.100");
    let items = updates(&body);
    let mut elements: Vec<Vec<u8>> = items.iter().map(|item| item.raw.to_vec()).collect();
    // drop `message.chat` from the first message update from element 37 on
    let k = (37..100)
        .find(|&k| {
            elements[k]
                .starts_with(format!(r#"{{"update_id":{},"message":{{"#, 30_001 + k).as_bytes())
        })
        .unwrap();
    let broken = std::str::from_utf8(&elements[k]).unwrap().to_owned();
    let at = broken.find(r#""chat":{"#).unwrap();
    let end = value_end(broken.as_bytes(), at + 7).unwrap();
    let broken = format!("{}{}", &broken[..at], &broken[end + 1..]);
    elements[k] = broken.clone().into_bytes();
    let refs: Vec<&[u8]> = elements.iter().map(Vec::as_slice).collect();

    let items = updates(&batch(&refs));
    assert_eq!(items.len(), 100);
    assert_eq!(items.iter().filter(|item| item.data.is_ok()).count(), 99);
    let failed: &UpdateError = items[k].data.as_ref().unwrap_err();
    assert_eq!(failed.update_id, Some(30_001 + i64::try_from(k).unwrap()));
    assert_eq!(failed.error.kind(), &ErrorKind::Missing);
    assert_eq!(failed.error.path(), "message.chat");
    assert_eq!(&*items[k].raw, broken.as_bytes());
    assert!(items[k + 1].data.is_ok());
}

#[test]
fn unknown_tag_in_a_batch_decodes_every_element() {
    // 10 §1, ported: on 3.x this batch fails as a whole and polling retries it forever
    let small = trimmed("update.text.small");
    let tag = trimmed("update.unknown-tag");
    let items = updates(&batch(&[&small, &tag]));
    assert_eq!(items.len(), 2);
    assert!(items[0].data.as_ref().unwrap().message.is_some());
    let updated = items[1]
        .data
        .as_ref()
        .unwrap()
        .chat_member
        .as_deref()
        .unwrap();
    let ChatMember::Unknown(unknown) = &updated.new_chat_member else {
        panic!("{:?}", updated.new_chat_member)
    };
    assert_eq!(unknown.tag.as_deref(), Some("superadmin"));
    assert_eq!(&*items[1].raw, &tag[..]);
}

#[test]
fn deep_and_surrogate_elements_do_not_fail_the_batch() {
    let small = trimmed("update.text.small");
    let deep = format!(r#"{{"update_id":7,"message":{}}}"#, chain(10_000));
    let surrogate = br#"{"message":{"message_id":1,"date":1,"chat":{"id":1,"type":"private"},"text":"\ud800"},"update_id":8}"#;
    let body = batch(&[&small, deep.as_bytes(), surrogate, &small]);
    let items = std::thread::Builder::new()
        .stack_size(256 * 1024)
        .spawn(move || updates(&body))
        .unwrap()
        .join()
        .unwrap();
    assert_eq!(items.len(), 4);
    assert!(items[0].data.is_ok() && items[3].data.is_ok());
    let deep_error = items[1].data.as_ref().unwrap_err();
    assert_eq!(
        (deep_error.update_id, deep_error.error.kind()),
        (Some(7), &ErrorKind::Depth)
    );
    assert_eq!(items[1].raw.len(), deep.len());
    let bad = items[2].data.as_ref().unwrap_err();
    assert_eq!(bad.update_id, Some(8));
    assert!(matches!(bad.error.kind(), ErrorKind::Json(_)));
    assert_eq!(&*items[2].raw, surrogate);
}

#[test]
fn unbalanced_element_fails_the_body() {
    let small = trimmed("update.text.small");
    let body = batch(&[&small, br#"{"update_id":2,"message":{"a":[}"#]);
    let error = decode_updates::<Update>(&body, LENIENT).unwrap_err();
    // the scanner balanced it against the envelope's own `]}`, so the body ends early
    assert!(
        error.error.path().starts_with("result[1]"),
        "{}",
        error.error
    );
    assert!(error.result.is_none());
    // and so does broken JSON between the elements
    let body = br#"{"ok":true,"result":[{"update_id":1} {"update_id":2}]}"#;
    let error = decode_updates::<Update>(body, LENIENT).unwrap_err();
    assert_eq!(error.error.path(), "result[0]");
}

#[test]
fn empty_batch() {
    assert!(updates(br#"{"ok":true,"result":[]}"#).is_empty());
}

#[test]
fn error_envelopes() {
    let body = corpus("response.error.400");
    let Response::Err(error) = decode_updates::<Update>(&body, LENIENT).unwrap().value else {
        panic!()
    };
    assert_eq!(error.error_code, Some(400));
    assert_eq!(
        error.description.as_deref(),
        Some("Bad Request: message text is empty")
    );
    assert!(error.parameters.is_none());

    let body = corpus("response.error.429");
    let Response::Err(error) = decode_response(&body, |c| c.bool(), LENIENT).unwrap().value else {
        panic!()
    };
    assert_eq!(error.error_code, Some(429));
    assert_eq!(
        text(&body, error.parameters.unwrap()),
        r#"{"retry_after":5}"#
    );

    let Response::Err(error) = decode_response(br#"{"ok":false}"#, |c| c.bool(), LENIENT)
        .unwrap()
        .value
    else {
        panic!()
    };
    let error: ApiError = error;
    assert!(error.error_code.is_none() && error.description.is_none());
}

#[test]
fn ok_results() {
    let body = corpus("response.ok-null-result");
    let decoded = decode_response(&body, |c| c.opt(|c| c.bool()), LENIENT).unwrap();
    assert!(matches!(decoded.value, Response::Ok(None)));

    let body = corpus("response.sendMessage");
    let Response::Ok(msg) = decode_response(&body, Message::decode, LENIENT)
        .unwrap()
        .value
    else {
        panic!()
    };
    assert_eq!(msg.message_id, 5014);
    // offsets index the body: the result is decoded in place
    assert!(text(&body, msg.meta.span).starts_with(r#"{"message_id":5014,"#));

    let body = br#" {"description":"x","extra":[1],"result":true,"ok":true} "#;
    assert!(matches!(
        decode_response(body, |c| c.bool(), LENIENT).unwrap().value,
        Response::Ok(true)
    ));
}

#[test]
fn body_errors() {
    let error = |body: &[u8]| decode_response(body, Message::decode, LENIENT).unwrap_err();
    let missing = error(br#"{"ok":true}"#);
    assert_eq!(
        (missing.error.kind(), missing.error.path().as_str()),
        (&ErrorKind::Missing, "result")
    );
    let missing = error(br#"{"result":1}"#);
    assert_eq!(missing.error.path(), "result");
    let missing = error(br#"{"ok":null,"result":true}"#);
    assert_eq!(missing.error.path(), "result");

    let body = br#"{"ok":true,"result":{"message_id":"x","date":1},"z":1}"#;
    let BodyError { error, result } = error(body);
    assert_eq!(error.path(), "result.message_id");
    assert_eq!(
        text(body, result.unwrap()),
        r#"{"message_id":"x","date":1}"#
    );

    assert!(error_is_json(br#"{"ok":true,"result":true} x"#));
    assert!(error_is_json(br#"{"ok":true,"result":tru}"#));
    assert!(error_is_json(b"[1]"));
    assert!(error_is_json(b"{\"ok\":\xff}"));
}

fn error_is_json(body: &[u8]) -> bool {
    let error = decode_response(body, |c| c.bool(), LENIENT).unwrap_err();
    matches!(error.error.kind(), ErrorKind::Json(_))
}

#[test]
fn single_update_body() {
    let raw: Arc<[u8]> = corpus("update.text.small").into();
    let item = decode_update::<Update>(raw.clone(), LENIENT).value;
    assert_eq!(item.data.unwrap().update_id, 10_001);
    assert!(Arc::ptr_eq(&item.raw, &raw));

    let raw: Arc<[u8]> = Arc::from(&br#"{"update_id":5,"message":{"message_id":1}}"#[..]);
    let item = decode_update::<Update>(raw, LENIENT).value;
    let error = item.data.unwrap_err();
    assert_eq!(
        (error.update_id, error.error.path().as_str()),
        (Some(5), "message.date")
    );

    let raw: Arc<[u8]> = Arc::from(&b"{\"update_id\":6,\"x\":\"\xff\"}"[..]);
    let error = decode_update::<Update>(raw, LENIENT)
        .value
        .data
        .unwrap_err();
    assert_eq!(error.update_id, Some(6));

    let raw: Arc<[u8]> = Arc::from(&br#"{"update_id":7} {}"#[..]);
    assert!(decode_update::<Update>(raw, LENIENT).value.data.is_err());
}

#[test]
fn first_seen_and_strict_through_the_entry_points() {
    let element = br#"{"update_id":1,"message":{"message_id":1,"date":1,"chat":{"id":1,"type":"envtest-chat"}}}"#;
    let body = batch(&[element, element]);
    let decoded = decode_updates::<Update>(&body, LENIENT).unwrap();
    assert_eq!(
        decoded.first_seen,
        [Seen::new("ChatType", Site::Enum, "envtest-chat")]
    );

    let Response::Ok(items) = decode_updates::<Update>(&body, Options { strict: true })
        .unwrap()
        .value
    else {
        panic!()
    };
    // strict fails the update, not the batch: D-09 decides what to raise
    for item in items.iter() {
        let error = item.data.as_ref().unwrap_err();
        assert!(matches!(error.error.kind(), ErrorKind::Strict(_)));
        assert_eq!(error.update_id, Some(1));
    }

    let raw: Arc<[u8]> = Arc::from(&br#"{"update_id":2,"envtest_update":{}}"#[..]);
    let decoded = decode_update::<Update>(raw, LENIENT);
    assert_eq!(
        decoded.first_seen,
        [Seen::new("Update", Site::UpdateType, "envtest_update")]
    );
}

#[test]
fn retained_update_does_not_pin_the_batch() {
    let before = live();
    let body = corpus("response.getUpdates.100");
    let body_len = isize::try_from(body.len()).unwrap();
    let body_range = body.as_ptr_range();
    let kept = updates(&body).swap_remove(1);
    let kept_range = kept.raw.as_ptr_range();
    assert!(kept_range.end <= body_range.start || kept_range.start >= body_range.end);
    drop(body);
    assert_eq!(Arc::strong_count(&kept.raw), 1);
    let retained = live() - before;
    // the element (2.5 KB of bytes plus its tree) is all that is left of a 150 KB batch
    assert!(
        retained > 0 && retained < body_len / 10,
        "{retained} of {body_len}"
    );
    assert!(kept.data.is_ok());
    drop(kept);
}

#[test]
fn entry_points_are_send() {
    // what `py.detach` needs (07 §2): the closure and its result cross into a detached section
    fn detachable<R: Send>(f: impl FnOnce() -> R + Send) -> R {
        f()
    }
    let body = corpus("response.getUpdates.100");
    let decoded: BodyResult<Box<[Item<Update>]>> =
        detachable(|| decode_updates::<Update>(&body, LENIENT));
    assert!(decoded.is_ok());
    let raw: Arc<[u8]> = body.into();
    let _: Decoded<Item<Update>> = detachable(move || decode_update::<Update>(raw, LENIENT));
}
