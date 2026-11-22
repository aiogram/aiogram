//! The depth guard (13 B7, B19). Deep inputs are built in memory and run on spawned threads
//! with an explicit stack, so a regression crashes one test thread, not the whole run.

use super::corpus::corpus;
use super::types::{Message, Update};
use crate::decode::{Decode, ErrorKind, MAX_DEPTH};

/// `n` messages, each the `reply_to_message` of the one before. Decoded as a `Message`, the
/// innermost message is at depth `n` and its `chat` at `n + 1`.
pub(crate) fn chain(n: usize) -> String {
    let head = r#"{"message_id":1,"date":1,"chat":{"id":1,"type":"private"}"#;
    let mut out = String::with_capacity(n * (head.len() + 22));
    for _ in 1..n {
        out.push_str(head);
        out.push_str(r#","reply_to_message":"#);
    }
    out.push_str(head);
    for _ in 0..n {
        out.push('}');
    }
    out
}

fn on_stack<T: Send + 'static>(stack: usize, f: impl FnOnce() -> T + Send + 'static) -> T {
    std::thread::Builder::new()
        .stack_size(stack)
        .spawn(f)
        .unwrap()
        .join()
        .unwrap()
}

fn depth_of(msg: &Message) -> usize {
    let mut depth = 1;
    let mut next = msg.reply_to_message.as_deref();
    while let Some(reply) = next {
        depth += 1;
        next = reply.reply_to_message.as_deref();
    }
    depth + 1 // the innermost chat
}

#[test]
fn depth_128_decodes_and_129_fails() {
    let max = usize::from(MAX_DEPTH);
    let msg = Message::from_slice(chain(max - 1).as_bytes(), 0).unwrap();
    assert_eq!(depth_of(&msg), max);

    let error = Message::from_slice(chain(max).as_bytes(), 0).unwrap_err();
    assert_eq!(error.kind(), &ErrorKind::Depth);
    let path = error.path();
    assert_eq!(path.matches("reply_to_message").count(), max - 1);
    assert!(path.ends_with(".chat"), "{path}");
}

#[test]
fn deep_nesting_corpus_is_an_error() {
    // 200 `pinned_message` levels: the depth error is not absorbed by the union around it
    let error = Update::from_slice(&corpus("update.deep-nesting"), 0).unwrap_err();
    assert_eq!(error.kind(), &ErrorKind::Depth);
    assert!(
        error
            .path()
            .starts_with("message.pinned_message.pinned_message")
    );
}

#[test]
fn ten_thousand_deep_neither_crashes_nor_overflows() {
    for stack in [256 * 1024, 2 * 1024 * 1024] {
        let error = on_stack(stack, || {
            Message::from_slice(chain(10_000).as_bytes(), 0).unwrap_err()
        });
        assert_eq!(error.kind(), &ErrorKind::Depth);
    }
}

#[test]
fn deepest_tree_decodes_and_drops_on_a_small_stack() {
    let depth = on_stack(256 * 1024, || {
        let msg = Message::from_slice(chain(usize::from(MAX_DEPTH) - 1).as_bytes(), 0).unwrap();
        let depth = depth_of(&msg);
        drop(msg);
        depth
    });
    assert_eq!(depth, usize::from(MAX_DEPTH));
}

#[test]
fn depth_is_restored_after_each_object() {
    // 300 siblings of depth 3 each: only nesting counts
    let items = vec![r#"{"type":"bold","offset":0,"length":1}"#; 300].join(",");
    let json = super::wrap(&format!(
        r#","entities":[{items}],"reply_to_message":{}"#,
        chain(100)
    ));
    let msg = Message::from_slice(json.as_bytes(), 0).unwrap();
    assert_eq!(msg.entities.as_deref().unwrap().len(), 300);
    // nor do absorbed failures: every level has a malformed union member that failed two
    // objects further in (so the chain stops two short of the limit)
    let bad = r#","forward_origin":{"type":"user","date":1,"sender_user":{"id":"x"}}"#;
    let chain = chain(usize::from(MAX_DEPTH) - 2).replace(
        r#""type":"private"}"#,
        &format!(r#""type":"private"}}{bad}"#),
    );
    let msg = Message::from_slice(chain.as_bytes(), 0).unwrap();
    assert_eq!(depth_of(&msg), usize::from(MAX_DEPTH) - 1);
    assert!(matches!(
        msg.forward_origin(),
        Some(super::types::MessageOrigin::Unknown(_))
    ));
}

#[test]
fn depth_error_is_not_overwritten_by_a_later_duplicate() {
    // 150 levels: shallow enough that jiter could skip the value and let the duplicate win
    let json = super::wrap(&format!(
        r#","reply_to_message":{},"reply_to_message":{}"#,
        chain(150),
        chain(1)
    ));
    let error = Message::from_slice(json.as_bytes(), 0).unwrap_err();
    assert_eq!(error.kind(), &ErrorKind::Depth);
}
