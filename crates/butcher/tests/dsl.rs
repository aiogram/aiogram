// clippy.toml's allow-*-in-tests covers #[test] fns only, not the helpers of an integration test crate
#![allow(clippy::unwrap_used, clippy::panic)]

//! The fill-DSL (plan C-07): the parser, and the resolver on `tests/fixtures/dsl/`.
//!
//! The fixture is the 3.x data: `overlay/shortcuts/*.toml` are all 189 shortcuts of dev-4.x
//! `.butcher/types/*/aliases.yml` written in the DSL, and `ir.json` holds their types (only the fields the paths use)
//! and target methods (only the filled or ignored params), with types and requiredness from the `.butcher` entities.
//! Assertions never contain a path separator (Windows CI).

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use butcher::Error;
use butcher::dsl::{self, Expr, Helpers, Segment, Syntax, parse_expr, parse_path};
use butcher::ir::{FillValue, Filled, Ir, Shortcut, Step, TypeRef};
use butcher::overlay::Overlay;

fn fixture() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/dsl")
}

fn ir() -> Ir {
    Ir::load(&fixture().join("ir.json")).unwrap()
}

/// The two helpers of 3.x, until `*_ext.pyi` fragments declare them (B-10 / C-27).
fn helpers() -> Helpers {
    let reply = || {
        (
            "as_reply_parameters".to_owned(),
            TypeRef::Ref("ReplyParameters".to_owned()),
        )
    };
    let ephemeral = (
        "as_ephemeral_message_parameters".to_owned(),
        TypeRef::Ref("EphemeralMessageParameters".to_owned()),
    );
    BTreeMap::from([
        ("Message".to_owned(), BTreeMap::from([reply(), ephemeral])),
        ("InaccessibleMessage".to_owned(), BTreeMap::from([reply()])),
    ])
}

fn corpus() -> Ir {
    let overlay = Overlay::load(&fixture().join("overlay")).unwrap();
    let mut ir = ir();
    let errors = overlay.check(&ir);
    assert!(errors.is_empty(), "{errors:?}");
    dsl::apply(&mut ir, &overlay, &helpers()).unwrap();
    ir
}

fn shortcut<'a>(ir: &'a Ir, ty: &str, name: &str) -> &'a Shortcut {
    ir.shortcuts
        .iter()
        .find(|s| s.ty == ty && s.name == name)
        .unwrap()
}

fn path(fields: &[&str]) -> Vec<Step> {
    fields
        .iter()
        .map(|f| match f.strip_prefix('?') {
            Some(f) => Step {
                field: f.to_owned(),
                chain: true,
            },
            None => Step {
                field: (*f).to_owned(),
                chain: false,
            },
        })
        .collect()
}

fn value(fields: &[&str]) -> Filled {
    Filled {
        value: FillValue::Path(path(fields)),
        when: None,
    }
}

#[test]
fn every_legacy_shortcut_resolves() {
    let ir = corpus();
    assert_eq!(ir.shortcuts.len(), 189);
    assert_eq!(ir.events.len(), 4);
    let reparsed: Ir = serde_json::from_str(&ir.to_json().unwrap()).unwrap();
    assert_eq!(reparsed, ir);
}

#[test]
fn shape_path() {
    let ir = corpus();
    let answer = shortcut(&ir, "Message", "answer");
    assert_eq!(answer.method, "sendMessage");
    assert_eq!(answer.fill["chat_id"], value(&["chat", "id"]));
    assert_eq!(
        answer.fill["business_connection_id"],
        value(&["business_connection_id"])
    );
    assert_eq!(
        shortcut(&ir, "CallbackQuery", "answer").fill["callback_query_id"],
        value(&["id"])
    );
    assert_eq!(
        shortcut(&ir, "ChatJoinRequest", "approve").fill["user_id"],
        value(&["from", "id"])
    );
}

#[test]
fn shape_path_when_path() {
    let ir = corpus();
    let thread = &shortcut(&ir, "Message", "answer").fill["message_thread_id"];
    assert_eq!(thread.value, FillValue::Path(path(&["message_thread_id"])));
    assert_eq!(thread.when, Some(path(&["is_topic_message"])));
}

#[test]
fn shape_optional_chain() {
    let ir = corpus();
    let topic = &shortcut(&ir, "Message", "answer").fill["direct_messages_topic_id"];
    assert_eq!(*topic, value(&["direct_messages_topic", "?topic_id"]));
}

#[test]
fn shape_helper_call() {
    let ir = corpus();
    let reply = shortcut(&ir, "Message", "reply");
    assert_eq!(
        reply.fill["reply_parameters"].value,
        FillValue::Helper("as_reply_parameters".to_owned())
    );
    assert_eq!(
        reply.fill["ephemeral_message_parameters"].value,
        FillValue::Helper("as_ephemeral_message_parameters".to_owned())
    );
    assert_eq!(reply.ignore, ["reply_to_message_id", "receiver_user_id"]);
}

#[test]
fn shape_none_literal() {
    let ir = corpus();
    let fill = &shortcut(&ir, "Message", "delete_reply_markup").fill["reply_markup"];
    assert_eq!(fill.value, FillValue::None);
}

#[test]
fn shape_guards() {
    let ir = corpus();
    let delete = shortcut(&ir, "Message", "delete");
    assert_eq!(delete.require[0].path, path(&["chat"]));
    assert_eq!(delete.forbid[0].path, path(&["business_connection_id"]));
    assert!(delete.forbid[0].message.contains("business messages"));
    // a later guard and the fill rely on the earlier `require`
    let ephemeral = ir.shortcuts.iter().find(|s| s.require.len() == 3).unwrap();
    assert_eq!(ephemeral.require[1].path, path(&["receiver_user"]));
}

#[test]
fn event_contexts_resolve() {
    let ir = corpus();
    let callback = ir
        .events
        .iter()
        .find(|e| e.update == "callback_query")
        .unwrap();
    assert_eq!(callback.user, Some(value(&["from"])));
    assert_eq!(callback.chat, Some(value(&["message", "?chat"])));
    let thread = callback.thread_id.as_ref().unwrap();
    assert_eq!(thread.when, Some(path(&["message", "?is_topic_message"])));
    let poll = ir
        .events
        .iter()
        .find(|e| e.update == "poll_answer")
        .unwrap();
    assert_eq!(poll.chat, Some(value(&["voter_chat"])));
    assert_eq!(poll.thread_id, None);
}

#[test]
fn the_parser_reads_every_form() {
    let seg = |name: &str, chain, column| Segment {
        name: name.to_owned(),
        chain,
        column,
    };
    assert_eq!(parse_expr("None"), Ok(Expr::None));
    assert_eq!(
        parse_expr("self.a.b?.c_1"),
        Ok(Expr::Path(vec![
            seg("a", false, 6),
            seg("b", false, 8),
            seg("c_1", true, 11)
        ]))
    );
    assert_eq!(
        parse_expr("self.as_x()"),
        Ok(Expr::Helper {
            name: "as_x".to_owned(),
            column: 6
        })
    );
    assert_eq!(parse_path("self._a"), Ok(vec![seg("_a", false, 6)]));
}

#[test]
fn a_syntax_error_has_its_column() {
    fn err<T>(column: usize, message: &str) -> Result<T, Syntax> {
        Err(Syntax {
            column,
            message: message.to_owned(),
        })
    }
    let expected = "expected `self.<field>`, `self.<helper>()` or `None`";
    assert_eq!(parse_expr("chat.id"), err(1, expected));
    assert_eq!(parse_expr(" self.chat"), err(1, expected));
    assert_eq!(
        parse_path("None"),
        err(1, "expected a path, `self.<field>`")
    );
    assert_eq!(parse_expr("self."), err(6, "expected a name"));
    assert_eq!(parse_expr("self.chat..id"), err(11, "expected a name"));
    assert_eq!(parse_expr("self.1a"), err(6, "expected a name"));
    assert_eq!(
        parse_expr("self.chat .id"),
        err(10, "unexpected ` `: expected `.`, `?.`, `()` or the end")
    );
    assert_eq!(
        parse_expr("self.chat?id"),
        err(10, "unexpected `?`: expected `.`, `?.`, `()` or the end")
    );
    assert_eq!(parse_path("self.f()"), err(7, "a call is not allowed here"));
    assert_eq!(
        parse_expr("self.chat.f()"),
        err(12, "only `self.<helper>()` can be called")
    );
    assert_eq!(
        parse_expr("self.f().id"),
        err(9, "expected the end after `()`")
    );
}

/// `(file name, key path, message)` of every error `apply` reports for `files`, next to the fixture's `names.toml`.
fn errors(name: &str, files: &[(&str, &str)]) -> Vec<(String, String, String)> {
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR"))
        .join("dsl")
        .join(name);
    let _ = std::fs::remove_dir_all(&dir);
    for (rel, text) in files {
        let path = dir.join(rel);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, text).unwrap();
    }
    let names = fixture().join("overlay/names.toml");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::copy(names, dir.join("names.toml")).unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    let mut ir = ir();
    let before = ir.clone();
    let errors = dsl::apply(&mut ir, &overlay, &helpers()).unwrap_err();
    assert_eq!(ir, before, "a failed apply leaves the IR unchanged");
    errors
        .iter()
        .map(|e| match e {
            Error::Parse { path, at, message } => (
                path.file_name().unwrap().to_string_lossy().into_owned(),
                at.clone(),
                message.clone(),
            ),
            other => panic!("not a parse error: {other}"),
        })
        .collect()
}

fn one(name: &str, file: &str, text: &str) -> (String, String) {
    let mut errors = errors(name, &[(file, text)]);
    assert_eq!(errors.len(), 1, "{errors:?}");
    let (_, at, message) = errors.remove(0);
    (at, message)
}

fn message_shortcut(name: &str, text: &str) -> (String, String) {
    one(name, "shortcuts/Message.toml", text)
}

fn pair(at: &str, message: &str) -> (String, String) {
    (at.to_owned(), message.to_owned())
}

#[test]
fn a_fill_key_that_is_not_a_param_names_the_key_and_method() {
    let text = "[answer]\nmethod = \"sendMessage\"\n[answer.fill]\nchat_idd = \"self.chat.id\"\n";
    let err = message_shortcut("not-a-param", text);
    let message = "`chat_idd` is not a param of `sendMessage` (closest: `chat_id`)";
    assert_eq!(err, pair("answer.fill.chat_idd", message));
}

#[test]
fn a_path_through_a_removed_field_names_it_and_the_ledger() {
    let text = "[answer]\nmethod = \"sendMessage\"\n[answer.fill]\nchat_id = \"self.chat.idd\"\n";
    let err = message_shortcut("removed", text);
    let message = "column 11: `Chat` has no field `idd` (closest: `id`); if it was removed upstream, keep it with a \
                   `removed_field` entry in `butcher/ledger.toml`, or change this path";
    assert_eq!(err, pair("answer.fill.chat_id", message));
}

#[test]
fn a_wire_name_is_not_a_python_name() {
    let text = "[approve]\nmethod = \"approveChatJoinRequest\"\n[approve.fill]\nuser_id = \"self.from.id\"\n";
    let (at, message) = one("wire-name", "shortcuts/ChatJoinRequest.toml", text);
    assert_eq!(at, "approve.fill.user_id");
    assert!(
        message.starts_with("column 6: `ChatJoinRequest` has no field `from`;"),
        "{message}"
    );
}

#[test]
fn a_step_after_an_optional_field_needs_a_guard_or_a_chain() {
    let text =
        "[x]\nmethod = \"sendMessage\"\n[x.fill]\nreceiver_user_id = \"self.receiver_user.id\"\n";
    let message =
        "column 20: `self.receiver_user` may be None: add a `require` guard or write `?.`";
    assert_eq!(
        message_shortcut("unguarded", text),
        pair("x.fill.receiver_user_id", message)
    );
}

#[test]
fn a_guard_takes_no_chain_and_may_fail_itself() {
    let text = "[x]\nmethod = \"sendMessage\"\nrequire = [{ path = \"self.chat?.id\", message = \"m\" }]\n\
                forbid = [{ path = \"self.receiver_user.id\", message = \"m\" }, { path = \"chat\", message = \"m\" }]\n";
    let errors = errors("guards", &[("shortcuts/Message.toml", text)]);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair("x.require[0].path", "column 10: a guard takes no `?.`"),
            pair(
                "x.forbid[0].path",
                "column 20: `self.receiver_user` may be None: add a `require` guard or write `?.`"
            ),
            pair(
                "x.forbid[1].path",
                "column 1: expected a path, `self.<field>`"
            ),
        ]
    );
}

#[test]
fn a_value_that_may_be_none_cannot_fill_a_required_param() {
    let text = "[x]\nmethod = \"deleteMessage\"\n[x.fill]\nmessage_id = \"self.message_thread_id\"\nchat_id = \"None\"\n";
    let errors = errors("nullable", &[("shortcuts/Message.toml", text)]);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair(
                "x.fill.chat_id",
                "column 1: `chat_id` of `deleteMessage` is required and cannot be `None`"
            ),
            pair(
                "x.fill.message_id",
                "column 1: `message_id` of `deleteMessage` is required, but the value may be None"
            ),
        ]
    );
    // `?.` after a field that is never None keeps the value non-null
    let text = "[x]\nmethod = \"approveChatJoinRequest\"\n[x.fill]\nuser_id = \"self.from_user?.id\"\nchat_id = \"self.chat?.id\"\n";
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR")).join("dsl/needless-chain");
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(dir.join("shortcuts")).unwrap();
    std::fs::copy(fixture().join("overlay/names.toml"), dir.join("names.toml")).unwrap();
    std::fs::write(dir.join("shortcuts/ChatJoinRequest.toml"), text).unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    dsl::apply(&mut ir(), &overlay, &helpers()).unwrap();
}

#[test]
fn a_when_cannot_fill_a_required_param() {
    let text = "[x]\nmethod = \"approveChatJoinRequest\"\n[x.fill]\n\
                user_id = { expr = \"self.from_user.id\", when = \"self.chat\" }\n";
    let (at, message) = one("when-required", "shortcuts/ChatJoinRequest.toml", text);
    assert_eq!(at, "x.fill.user_id.expr");
    assert_eq!(
        message,
        "column 1: `user_id` of `approveChatJoinRequest` is required, but its `when` can omit it"
    );
}

#[test]
fn errors_in_a_when_or_its_expr_name_that_key() {
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\n\
                message_thread_id = { expr = \"self.message_thread_id\", when = \"self.is_topic\" }\n\
                business_connection_id = { expr = \"self.\", when = \"self.is_topic_message\" }\n\
                chat_id = { expr = \"self.chat.id\", when = \"self.chat.f()\" }\n";
    let errors = errors("when", &[("shortcuts/Message.toml", text)]);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair(
                "x.fill.business_connection_id.expr",
                "column 6: expected a name"
            ),
            pair(
                "x.fill.chat_id.when",
                "column 12: a call is not allowed here"
            ),
            pair(
                "x.fill.message_thread_id.when",
                "column 6: `Message` has no field `is_topic`; if it was removed \
                 upstream, keep it with a `removed_field` entry in `butcher/ledger.toml`, or change this path"
            ),
        ]
    );
}

#[test]
fn a_value_of_the_wrong_type_is_rejected() {
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\nchat_id = \"self.chat\"\n\
                message_thread_id = \"self.business_connection_id\"\n";
    let errors = errors("type", &[("shortcuts/Message.toml", text)]);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair(
                "x.fill.chat_id",
                "column 1: the value is `Chat` and cannot fill `chat_id` of `sendMessage` (`int or string`)"
            ),
            pair(
                "x.fill.message_thread_id",
                "column 1: the value is `string` and cannot fill `message_thread_id` of `sendMessage` (`int`)"
            ),
        ]
    );
}

#[test]
fn a_helper_must_be_declared() {
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\nreply_parameters = \"self.as_reply()\"\n";
    let message = "column 6: `Message` has no helper `as_reply()` (known: `as_ephemeral_message_parameters`, \
                   `as_reply_parameters`)";
    assert_eq!(
        message_shortcut("helper", text),
        pair("x.fill.reply_parameters", message)
    );
    let text =
        "[x]\nmethod = \"answerCallbackQuery\"\n[x.fill]\ncallback_query_id = \"self.as_id()\"\n";
    let (_, message) = one("no-helpers", "shortcuts/CallbackQuery.toml", text);
    assert_eq!(
        message,
        "column 6: `CallbackQuery` has no helper `as_id()` (no helpers are declared for `CallbackQuery`)"
    );
}

#[test]
fn a_union_step_needs_the_field_on_every_member_or_a_chain() {
    let text = "[callback_query]\nchat = \"self.message?.chat\"\nthread_id = \"self.message?.message_thread_id\"\n\
                business_connection_id = { expr = \"self.message?.date\", when = \"self.message?.nope\" }\n\
                [inline_query]\nuser = \"self.from_user.message\"\n";
    let mut files = vec![("events.toml", text)];
    let errors = errors("union", &files);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair(
                "callback_query.business_connection_id.when",
                "column 15: no member of `MaybeInaccessibleMessage` has a field `nope`; if it was removed upstream, \
                 keep it with a `removed_field` entry in `butcher/ledger.toml`, or change this path"
            ),
            pair(
                "inline_query.user",
                "column 16: `User` has no field `message`; if it was removed upstream, keep it with a \
                 `removed_field` entry in `butcher/ledger.toml`, or change this path"
            ),
        ]
    );
    // without a chain the step is rejected: `message` is optional, and only `Message` has `message_thread_id`
    let text = "[callback_query]\nthread_id = \"self.message.message_thread_id\"\n";
    files[0].1 = text;
    let (_, message) = one("union-plain", "events.toml", text);
    assert_eq!(
        message,
        "column 14: `self.message` may be None: add a `require` guard or write `?.`"
    );
}

#[test]
fn a_partial_union_field_without_a_chain_is_rejected() {
    // `require` makes `message` non-null; the `.` step still needs every member to have the field
    let text = "[x]\nmethod = \"answerCallbackQuery\"\nrequire = [{ path = \"self.message\", message = \"m\" }]\n\
                [x.fill]\ncallback_query_id = \"self.message.business_connection_id\"\n";
    let (_, message) = one("union-partial", "shortcuts/CallbackQuery.toml", text);
    assert_eq!(
        message,
        "column 14: `business_connection_id` is not a field of every member of `MaybeInaccessibleMessage` \
         (missing on `InaccessibleMessage`): write `?.`"
    );
}

#[test]
fn a_step_into_a_value_without_fields_is_rejected() {
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\nchat_id = \"self.chat.id.x\"\n";
    let message = "column 14: `self.chat.id` is `int`, which has no fields";
    assert_eq!(
        message_shortcut("no-fields", text),
        pair("x.fill.chat_id", message)
    );
}

#[test]
fn an_event_value_must_have_the_slot_type() {
    let text = "[message]\nuser = \"self.chat\"\nchat = { expr = \"self.from_user\", when = \"self.is_topic_message\" }\n\
                thread_id = \"None\"\n[nope]\n";
    let errors = errors("event-type", &[("events.toml", text)]);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair(
                "message.user",
                "column 1: the value is `Chat` and cannot be the event `user` (`User`)"
            ),
            pair(
                "message.chat.expr",
                "column 1: the value is `User` and cannot be the event `chat` (`Chat`)"
            ),
            pair("nope", "no update type `nope`"),
        ]
    );
}

#[test]
fn unknown_types_methods_and_ignored_params_are_reported() {
    let errors = errors(
        "unknown",
        &[
            ("shortcuts/Nope.toml", "[x]\nmethod = \"sendMessage\"\n"),
            (
                "shortcuts/Message.toml",
                "[a]\nmethod = \"sendNope\"\n[b]\nignore = []\n[c]\nhandwritten = true\n\
                 [d]\nmethod = \"sendMessage\"\nignore = [\"nope\"]\n",
            ),
        ],
    );
    let errors: Vec<(String, String, String)> = errors;
    assert_eq!(
        errors,
        [
            (
                "Message.toml".to_owned(),
                "a.method".to_owned(),
                "no method `sendNope`".to_owned()
            ),
            (
                "Message.toml".to_owned(),
                "b".to_owned(),
                "needs `method` (or `handwritten = true`)".to_owned()
            ),
            (
                "Message.toml".to_owned(),
                "d.ignore[0]".to_owned(),
                "`nope` is not a param of `sendMessage`".to_owned()
            ),
            (
                "Nope.toml".to_owned(),
                ".".to_owned(),
                "no type `Nope`".to_owned()
            ),
        ]
    );
}

#[test]
fn types_are_assignable_by_the_wire_rules() {
    // int64 to `Integer or String`, `true` to bool, a union member to its union, arrays element-wise
    let mut ir = ir();
    let message = ir.types.iter_mut().find(|t| t.name == "Message").unwrap();
    let field = |name: &str, ty: TypeRef| -> butcher::ir::Field {
        serde_json::from_value(serde_json::json!({
            "name": name,
            "type": { "value": ty },
            "response": { "required": { "value": true } }
        }))
        .unwrap()
    };
    message
        .fields
        .push(field("x_int64", TypeRef::Prim(butcher::ir::Prim::Int64)));
    message
        .fields
        .push(field("x_true", TypeRef::Prim(butcher::ir::Prim::True)));
    message
        .fields
        .push(field("x_member", TypeRef::Ref("Message".to_owned())));
    let ints = TypeRef::Array(Box::new(TypeRef::Prim(butcher::ir::Prim::Int32)));
    message.fields.push(field("x_ints", ints));
    let union = TypeRef::Union(vec![
        TypeRef::Prim(butcher::ir::Prim::Int),
        TypeRef::Prim(butcher::ir::Prim::String),
    ]);
    message.fields.push(field("x_union", union));
    let param = |name: &str, ty: TypeRef| -> butcher::ir::Param {
        serde_json::from_value(serde_json::json!({
            "name": name,
            "type": { "value": ty },
            "required": { "value": true }
        }))
        .unwrap()
    };
    let method = ir
        .methods
        .iter_mut()
        .find(|m| m.name == "sendMessage")
        .unwrap();
    method
        .params
        .push(param("p_bool", TypeRef::Prim(butcher::ir::Prim::Bool)));
    method.params.push(param(
        "p_maybe",
        TypeRef::Ref("MaybeInaccessibleMessage".to_owned()),
    ));
    let longs = TypeRef::Array(Box::new(TypeRef::Prim(butcher::ir::Prim::Int64)));
    method.params.push(param("p_longs", longs));
    method
        .params
        .push(param("p_string", TypeRef::Prim(butcher::ir::Prim::String)));
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR")).join("dsl/assignable");
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(dir.join("shortcuts")).unwrap();
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\nchat_id = \"self.x_int64\"\np_bool = \"self.x_true\"\n\
                p_maybe = \"self.x_member\"\np_longs = \"self.x_ints\"\n";
    std::fs::write(dir.join("shortcuts/Message.toml"), text).unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    dsl::apply(&mut ir, &overlay, &helpers()).unwrap();
    assert_eq!(ir.shortcuts[0].fill.len(), 4);
    // a union value needs every member assignable
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\np_string = \"self.x_union\"\n";
    std::fs::write(dir.join("shortcuts/Message.toml"), text).unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    let errors = dsl::apply(&mut ir, &overlay, &helpers()).unwrap_err();
    assert!(errors[0].to_string().ends_with(
        "the value is `int or string` and cannot fill `p_string` of `sendMessage` (`string`)"
    ));
}

#[test]
fn a_union_field_must_have_one_type_on_every_member() {
    let mut ir = ir();
    let other = ir
        .types
        .iter_mut()
        .find(|t| t.name == "InaccessibleMessage")
        .unwrap();
    let date = other.fields.iter_mut().find(|f| f.name == "date").unwrap();
    date.ty.value = TypeRef::Prim(butcher::ir::Prim::String);
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR")).join("dsl/union-types");
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("events.toml"),
        "[callback_query]\nthread_id = \"self.message?.date\"\n",
    )
    .unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    let errors = dsl::apply(&mut ir, &overlay, &helpers()).unwrap_err();
    assert!(errors[0].to_string().ends_with(
        "callback_query.thread_id: column 15: `date` has a different type on the members of `MaybeInaccessibleMessage`"
    ), "{}", errors[0]);
}

#[test]
fn a_step_into_a_type_missing_from_the_ir_is_rejected() {
    // an enum, or a type the IR does not hold: a `Ref` that is neither a type nor a union
    let mut ir = ir();
    let chat = ir.types.iter_mut().find(|t| t.name == "Chat").unwrap();
    chat.fields[0].ty.value = TypeRef::Ref("ChatType".to_owned());
    let name = chat.fields[0].name.clone();
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR")).join("dsl/missing-type");
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    let text = format!("[message]\nuser = \"self.chat.{name}.x\"\n");
    std::fs::write(dir.join("events.toml"), text).unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    let errors = dsl::apply(&mut ir, &overlay, &helpers()).unwrap_err();
    let expected = format!("`self.chat.{name}` is `ChatType`, which has no fields");
    assert!(errors[0].to_string().ends_with(&expected), "{}", errors[0]);
}

#[test]
fn a_required_param_cannot_be_ignored_and_a_forbid_must_be_able_to_pass() {
    let text = "[x]\nmethod = \"deleteMessage\"\nignore = [\"message_id\"]\n\
                require = [{ path = \"self.business_connection_id\", message = \"m\" }]\n\
                forbid = [{ path = \"self.chat\", message = \"m\" }, { path = \"self.business_connection_id\", message = \"m\" }]\n";
    let errors = errors("ignore-forbid", &[("shortcuts/Message.toml", text)]);
    let errors: Vec<(String, String)> = errors.into_iter().map(|(_, a, m)| (a, m)).collect();
    assert_eq!(
        errors,
        [
            pair(
                "x.forbid[0].path",
                "column 1: `self.chat` is never None here, so this guard always raises"
            ),
            pair(
                "x.forbid[1].path",
                "column 1: `self.business_connection_id` is never None here, so this guard always raises"
            ),
            pair(
                "x.ignore[0]",
                "`message_id` of `deleteMessage` is required and cannot be ignored"
            ),
        ]
    );
}

#[test]
fn an_unknown_param_still_reports_the_errors_of_its_value() {
    let text = "[x]\nmethod = \"sendMessage\"\n[x.fill]\nchat_idd = \"self.chta.id\"\n";
    let errors = errors("both-errors", &[("shortcuts/Message.toml", text)]);
    assert_eq!(errors.len(), 2, "{errors:?}");
    assert!(errors[0].2.starts_with("`chat_idd` is not a param"));
    assert!(
        errors[1]
            .2
            .starts_with("column 6: `Message` has no field `chta`")
    );
}

fn union_ir(edit: impl FnOnce(&mut Ir)) -> Vec<String> {
    let mut ir = ir();
    edit(&mut ir);
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR")).join("dsl/union-shape");
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("events.toml"),
        "[callback_query]\nthread_id = \"self.message?.date\"\n",
    )
    .unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    match dsl::apply(&mut ir, &overlay, &helpers()) {
        Ok(()) => vec![],
        Err(errors) => errors.iter().map(ToString::to_string).collect(),
    }
}

#[test]
fn a_union_member_missing_from_the_ir_is_an_error() {
    let errors = union_ir(|ir| {
        ir.unions[0].members.value.push("Nope".to_owned());
    });
    assert!(
        errors[0].ends_with(
            "column 15: `MaybeInaccessibleMessage` has members that are not types in the IR: `Nope`"
        ),
        "{errors:?}"
    );
}

#[test]
fn a_union_step_must_read_one_wire_field() {
    // `names.toml` maps `ident` to `message_id` on one member and to `date` on the other
    let mut ir = ir();
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR")).join("dsl/union-wire");
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("events.toml"),
        "[callback_query]\nthread_id = \"self.message?.ident\"\n",
    )
    .unwrap();
    let names =
        "[types.Message]\nmessage_id = \"ident\"\n[types.InaccessibleMessage]\ndate = \"ident\"\n";
    std::fs::write(dir.join("names.toml"), names).unwrap();
    let overlay = Overlay::load(&dir).unwrap();
    let errors = dsl::apply(&mut ir, &overlay, &helpers()).unwrap_err();
    assert!(errors[0].to_string().ends_with(
        "column 15: `ident` is a different wire field on the members of `MaybeInaccessibleMessage` \
         (`message_id`, `date`): one step reads one field"
    ), "{}", errors[0]);
}
