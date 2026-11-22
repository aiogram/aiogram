// clippy.toml's allow-*-in-tests covers #[test] fns only, not the helpers of an integration test crate
#![allow(clippy::unwrap_used, clippy::panic)]

//! The overlay loader (plan C-06): one valid file, one unknown key and one dangling reference per kind, the digest.
//! Assertions never contain a path separator (Windows CI): they compare file names, key paths and messages.

use std::path::{Path, PathBuf};

use butcher::Error;
use butcher::ir::{Ir, Source};
use butcher::overlay::{self, Overlay};

/// Every kind, valid against `tests/fixtures/overlay/ir.json`.
const VALID: &[(&str, &str)] = &[
    (
        "names.toml",
        r#"
[types.Message]
from = "from_user"
[types.ManagedBotCreated]
bot = "bot_user"
[methods.sendMessage]
chat_id = "chat_id"
[union_aliases.sendMessage]
chat_id = "ChatIdUnion"
"#,
    ),
    (
        "enums/ChatType.toml",
        r#"
doc = "Chat type"
[parse]
type = "Chat"
field = "type"
regexp = "'([a-z]+)'"
[static]
SENDER = "sender"
"#,
    ),
    (
        "enums/ParseMode.toml",
        r#"
[parse]
method = "sendMessage"
field = "parse_mode"
regexp = "'([A-Za-z]+)'"
"#,
    ),
    (
        "enums/MessageOrigin.toml",
        r#"
[multi_parse]
field = "date"
regexp = "must be ([a-z_]+)"
types = ["Message", "InaccessibleMessage"]
"#,
    ),
    (
        "enums/UpdateType.toml",
        r#"
[extract]
type = "Update"
exclude = ["update_id"]
"#,
    ),
    (
        "datetime.toml",
        r#"
[types]
Message = ["date", "edit_date"]
"#,
    ),
    (
        "defaults.toml",
        r#"
[methods.sendMessage]
parse_mode = "parse_mode"
"#,
    ),
    (
        "shortcuts/Message.toml",
        r#"
[answer]
method = "sendMessage"
require = [{ path = "self.chat", message = "chat is required" }]
forbid = []
ignore = ["reply_to_message_id"]
[answer.fill]
chat_id = "self.chat.id"
message_thread_id = { expr = "self.message_thread_id", when = "self.is_topic_message" }

[get_url]
handwritten = true
"#,
    ),
    (
        "unions.toml",
        r#"
[MaybeInaccessibleMessage]
rules = [
  { member = "InaccessibleMessage", field = "date", eq = 0 },
  { member = "Message", field = "date", ne = 0 },
]
[ChatMember]
tag = "id"
"#,
    ),
    (
        "twins.toml",
        r#"
[ChatPermissions]
merge = true
[ChatPermissions.required]
can_send_media_messages = false
"#,
    ),
    (
        "layout.toml",
        r#"
[Message]
hot = ["message_id", "date", "chat", "from"]
[User]
freelist = true
"#,
    ),
    (
        "heuristics.toml",
        r#"
[returns]
getChatMember = { ref = "ChatMember" }
getUpdates = { array = { ref = "Update" } }
[consts.Chat]
type = "private"
[subtypes]
MaybeInaccessibleMessage = ["Message", "InaccessibleMessage"]
[enum_members]
ChatAction = ["typing"]
ChatType = ["private"]
"#,
    ),
    (
        "docs.toml",
        r#"
[types.Message]
note = "See also :meth:`answer`."
[methods.getMe]
note = "Cheap."
"#,
    ),
    (
        "methods.toml",
        r#"
excluded = ["getUpdates"]
[idempotent]
getMe = true
sendMessage = false
"#,
    ),
    (
        "display.toml",
        r#"
[types]
Message = ["text", "caption"]
[methods]
# `chat_id` is `Integer or String`: a union holding a string counts
sendMessage = ["text", "chat_id"]
"#,
    ),
    (
        "content.toml",
        r#"
[[kind]]
name = "text"
field = "text"
[kind.copy]
method = "sendMessage"
[kind.copy.fill]
text = "self.text"

[[kind]]
name = "photo"
field = "photo"
"#,
    ),
    (
        "events.toml",
        r#"
[message]
user = "self.from"
chat = "self.chat"
thread_id = { expr = "self.message_thread_id", when = "self.is_topic_message" }
business_connection_id = "self.business_connection_id"
[edited_message]
"#,
    ),
    (
        "bases.toml",
        r#"
ChatFullInfo = ["Chat"]
"#,
    ),
    (
        "errors.toml",
        r#"
[names]
"Bad Request: message is not modified" = "MESSAGE_NOT_MODIFIED"
"Forbidden: bot was blocked by the user" = "BOT_BLOCKED"
"#,
    ),
    ("README.md", "# Overlay\n"),
];

fn ir() -> Ir {
    Ir::load(&Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/overlay/ir.json")).unwrap()
}

fn scratch(name: &str, files: &[(&str, &str)]) -> PathBuf {
    let dir = Path::new(env!("CARGO_TARGET_TMPDIR"))
        .join("overlay")
        .join(name);
    let _ = std::fs::remove_dir_all(&dir);
    for (rel, text) in files {
        let path = dir.join(rel);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, text).unwrap();
    }
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

/// `(file name, key path, message)`.
fn parts(e: &Error) -> (String, String, String) {
    match e {
        Error::Parse { path, at, message } => (
            path.file_name().unwrap().to_string_lossy().into_owned(),
            at.clone(),
            message.clone(),
        ),
        other => panic!("not a parse error: {other}"),
    }
}

/// `VALID` with `file` replaced by `text`.
fn with(file: &str, text: &str) -> Vec<(&'static str, String)> {
    VALID
        .iter()
        .map(|(f, t)| {
            (
                *f,
                if *f == file {
                    text.to_owned()
                } else {
                    (*t).to_owned()
                },
            )
        })
        .collect()
}

fn load(name: &str, files: &[(&str, String)]) -> Result<Overlay, Error> {
    let files: Vec<(&str, &str)> = files.iter().map(|(f, t)| (*f, t.as_str())).collect();
    Overlay::load(&scratch(name, &files))
}

#[test]
fn every_kind_loads_and_checks_clean() {
    let overlay = Overlay::load(&scratch("valid", VALID)).unwrap();
    let errors: Vec<String> = overlay.check(&ir()).iter().map(Error::to_string).collect();
    assert_eq!(errors, Vec::<String>::new());
    // spot checks that each file landed in its kind
    assert_eq!(overlay.names.types["Message"]["from"], "from_user");
    assert_eq!(overlay.enums.len(), 4);
    assert!(overlay.enums["ChatType"].static_members.is_some());
    let answer = &overlay.shortcuts["Message"]["answer"];
    assert_eq!(answer.fill["chat_id"].expr, "self.chat.id");
    assert_eq!(answer.fill["chat_id"].when, None);
    let thread = &answer.fill["message_thread_id"];
    assert_eq!(thread.when.as_deref(), Some("self.is_topic_message"));
    assert!(overlay.shortcuts["Message"]["get_url"].handwritten);
    assert_eq!(overlay.unions["MaybeInaccessibleMessage"].rules.len(), 2);
    assert!(overlay.twins["ChatPermissions"].merge);
    assert!(overlay.layout["User"].freelist);
    assert_eq!(overlay.methods.excluded, ["getUpdates"]);
    let kinds: Vec<&str> = overlay
        .content
        .kind
        .iter()
        .map(|k| k.name.as_str())
        .collect();
    assert_eq!(kinds, ["text", "photo"], "content kinds keep file order");
    assert_eq!(overlay.events["edited_message"], Default::default());
    assert_eq!(overlay.bases["ChatFullInfo"], ["Chat"]);
    assert_eq!(overlay.errors.names.len(), 2);
    assert_eq!(overlay.datetime.types["Message"], ["date", "edit_date"]);
    assert_eq!(overlay.display.methods["sendMessage"], ["text", "chat_id"]);
    assert_eq!(overlay.docs.methods["getMe"].note, "Cheap.");
    assert_eq!(
        overlay.defaults.methods["sendMessage"]["parse_mode"],
        "parse_mode"
    );
    assert!(overlay.heuristics.returns.contains_key("getUpdates"));
}

#[test]
fn twin_merge_defaults_to_true_and_can_be_turned_off() {
    let files = with("twins.toml", "[ChatPermissions]\nmerge = false\n");
    assert!(!load("twin-off", &files).unwrap().twins["ChatPermissions"].merge);
    let files = with("twins.toml", "[ChatPermissions]\n");
    assert!(load("twin-default", &files).unwrap().twins["ChatPermissions"].merge);
}

#[test]
fn an_empty_or_missing_overlay_is_valid() {
    let overlay = Overlay::load(&scratch("empty", &[])).unwrap();
    assert!(overlay.check(&ir()).is_empty());
    assert!(overlay.enums.is_empty() && overlay.content.kind.is_empty());
}

/// One misspelt key per kind: `(file, text, key path)`.
const UNKNOWN: &[(&str, &str, &str)] = &[
    (
        "names.toml",
        "[type.Message]\nfrom = \"from_user\"\n",
        "type",
    ),
    (
        "enums/ChatType.toml",
        "[parse]\ntype = \"Chat\"\nfeild = \"type\"\nregexp = \"x\"\n",
        "parse.feild",
    ),
    ("datetime.toml", "[typs]\nMessage = [\"date\"]\n", "typs"),
    (
        "defaults.toml",
        "[method.sendMessage]\nparse_mode = \"parse_mode\"\n",
        "method",
    ),
    (
        "shortcuts/Message.toml",
        "[answer]\nmethod = \"sendMessage\"\nrequires = []\n",
        "answer.requires",
    ),
    // the fill table form keeps deny_unknown_fields
    (
        "shortcuts/Message.toml",
        "[answer]\nmethod = \"sendMessage\"\n[answer.fill]\nchat_id = { expr = \"self.chat.id\", whn = \"x\" }\n",
        "answer.fill.chat_id.whn",
    ),
    // the dead legacy key from `.butcher/types/MaybeInaccessibleMessage/subtypes.yml`
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\ntagged = true\ntag = \"date\"\n",
        "MaybeInaccessibleMessage.tagged",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\nrules = [{ member = \"Message\", field = \"date\", equals = 0 }]\n",
        "MaybeInaccessibleMessage.rules[0].equals",
    ),
    (
        "twins.toml",
        "[ChatPermissions]\nmerged = false\n",
        "ChatPermissions.merged",
    ),
    ("layout.toml", "[Message]\nhots = []\n", "Message.hots"),
    (
        "heuristics.toml",
        "[return]\ngetMe = { ref = \"User\" }\n",
        "return",
    ),
    (
        "docs.toml",
        "[types.Message]\nnotes = \"x\"\n",
        "types.Message.notes",
    ),
    ("methods.toml", "[idempotant]\ngetMe = true\n", "idempotant"),
    ("display.toml", "[type]\nMessage = [\"text\"]\n", "type"),
    (
        "content.toml",
        "[[kind]]\nname = \"text\"\nfield = \"text\"\ncopi = {}\n",
        "kind[0].copi",
    ),
    (
        "events.toml",
        "[message]\nusr = \"self.from\"\n",
        "message.usr",
    ),
    ("errors.toml", "[name]\n\"x\" = \"X\"\n", "name"),
];

#[test]
fn a_misspelt_key_fails_with_its_key_path() {
    for (i, (file, text, at)) in UNKNOWN.iter().enumerate() {
        let err = load(&format!("unknown-{i}"), &with(file, text)).unwrap_err();
        let (name, got_at, message) = parts(&err);
        assert_eq!(Path::new(file).file_name().unwrap().to_string_lossy(), name);
        assert_eq!(got_at, *at, "{file}: {err}");
        assert!(message.starts_with("unknown field"), "{file}: {message}");
        assert!(!message.contains('\n'), "one line: {message}");
        // `file:key.path: unknown field ...`
        assert!(
            err.to_string().contains(&format!(": {at}: unknown field")),
            "{err}"
        );
    }
}

#[test]
fn bases_takes_only_lists_of_names() {
    let err = load(
        "bases-shape",
        &with("bases.toml", "[ChatFullInfo]\nbase = \"Chat\"\n"),
    )
    .unwrap_err();
    assert_eq!(parts(&err).1, "ChatFullInfo");
}

#[test]
fn a_toml_syntax_error_keeps_its_position() {
    let err = load("syntax", &with("names.toml", "[types\n")).unwrap_err();
    let (_, at, message) = parts(&err);
    assert_eq!(at, ".");
    assert!(message.contains("line 1"), "{message}");
}

#[test]
fn a_fill_must_be_a_string_or_a_table() {
    let text = "[answer]\nmethod = \"sendMessage\"\n[answer.fill]\nchat_id = 1\n";
    let err = load("fill-int", &with("shortcuts/Message.toml", text)).unwrap_err();
    let (_, at, message) = parts(&err);
    assert_eq!(at, "answer.fill.chat_id");
    assert!(
        message.contains("a fill expression string or a table"),
        "{message}"
    );
}

#[test]
fn a_file_outside_the_layout_is_rejected() {
    for (i, stray) in [
        "name.toml",
        "enums/ChatType.yml",
        "shortcuts/sub/Message.toml",
        "notes.txt",
    ]
    .iter()
    .enumerate()
    {
        let mut files: Vec<(&str, &str)> = VALID.to_vec();
        files.push((stray, "x = 1\n"));
        let err = Overlay::load(&scratch(&format!("stray-{i}"), &files)).unwrap_err();
        let (_, at, message) = parts(&err);
        assert_eq!(at, ".", "{stray}");
        assert!(
            message.contains("not an overlay file") || message.contains("<Name>.toml"),
            "{stray}: {message}"
        );
    }
}

#[test]
fn a_missing_directory_is_an_io_error() {
    let dir = scratch("missing", &[]).join("nope");
    assert!(matches!(Overlay::load(&dir), Err(Error::Io { .. })));
    assert!(matches!(overlay::digest(&dir), Err(Error::Io { .. })));
}

/// One dangling reference (or broken rule) per kind: `(file, text, key path, message fragment)`.
const DANGLING: &[(&str, &str, &str, &str)] = &[
    (
        "names.toml",
        "[types.Message]\nfrm = \"from_user\"\n",
        "types.Message.frm",
        "no field on type `Message`: `frm` (closest: `from`)",
    ),
    (
        "names.toml",
        "[types.Mesage]\nfrom = \"from_user\"\n",
        "types.Mesage",
        "no type `Mesage` (closest: `Message`)",
    ),
    (
        "names.toml",
        "[methods.sendMessage]\nchat_id = \"class\"\n",
        "methods.sendMessage.chat_id",
        "not a Python identifier",
    ),
    (
        "names.toml",
        "[union_aliases.sendMesage]\nmedia = \"MediaUnion\"\n",
        "union_aliases.sendMesage",
        "no method `sendMesage` (closest: `sendMessage`)",
    ),
    (
        "names.toml",
        "[union_aliases.sendMessage]\nmedia = \"MediaUnion\"\n",
        "union_aliases.sendMessage.media",
        "no param of method `sendMessage`: `media`",
    ),
    (
        "enums/ChatType.toml",
        "[parse]\ntype = \"Chat\"\nfield = \"typ\"\nregexp = \"x\"\n",
        "parse.field",
        "(closest: `type`)",
    ),
    (
        "enums/ChatType.toml",
        "[parse]\ntype = \"Chat\"\nmethod = \"getMe\"\nfield = \"type\"\nregexp = \"x\"\n",
        "parse",
        "exactly one of `type`, `method`",
    ),
    (
        "enums/ChatType.toml",
        "[parse]\nmethod = \"sendMessage\"\nfield = \"mode\"\nregexp = \"x\"\n",
        "parse.field",
        "no param of method `sendMessage`: `mode`",
    ),
    (
        "enums/ChatType.toml",
        "[parse]\nmethod = \"sendMesage\"\nfield = \"mode\"\nregexp = \"x\"\n",
        "parse.method",
        "no method `sendMesage`",
    ),
    (
        "enums/ChatType.toml",
        "doc = \"x\"\n",
        ".",
        "needs at least one of",
    ),
    (
        "enums/ChatType.toml",
        "[static]\nSender = \"sender\"\n",
        "static.Sender",
        "UPPER_SNAKE_CASE",
    ),
    (
        "enums/ChatType.toml",
        "[multi_parse]\nfield = \"date\"\nregexp = \"x\"\ntypes = [\"Message\", \"Chat\"]\n",
        "multi_parse.types[1]",
        "no field on type `Chat`: `date`",
    ),
    (
        "enums/ChatType.toml",
        "[extract]\ntype = \"Update\"\nexclude = [\"updat_id\"]\n",
        "extract.exclude[0]",
        "(closest: `update_id`)",
    ),
    (
        "enums/ChatType.toml",
        "[extract]\ntype = \"Updat\"\n",
        "extract.type",
        "no type `Updat` (closest: `Update`)",
    ),
    (
        "datetime.toml",
        "[types]\nMessage = [\"date\", \"edit_dat\"]\n",
        "types.Message[1]",
        "no field on type `Message`: `edit_dat` (closest: `edit_date`)",
    ),
    (
        "datetime.toml",
        "[methods]\nsendMessage = [\"until_date\"]\n",
        "methods.sendMessage[0]",
        "no param of method `sendMessage`: `until_date`",
    ),
    (
        "defaults.toml",
        "[methods.sendMesage]\nparse_mode = \"parse_mode\"\n",
        "methods.sendMesage",
        "no method `sendMesage`",
    ),
    (
        "display.toml",
        "[types]\nMessage = [\"photo\"]\n",
        "types.Message[0]",
        "`Message.photo` is not a string field",
    ),
    (
        "display.toml",
        "[types]\nMessage = [\"chat\"]\n",
        "types.Message[0]",
        "`Message.chat` is not a string field",
    ),
    (
        "defaults.toml",
        "[types.Message]\ntext = \"9text\"\n",
        "types.Message.text",
        "not a Python identifier",
    ),
    (
        "defaults.toml",
        "[methods.sendMessage]\nparse_mod = \"parse_mode\"\n",
        "methods.sendMessage.parse_mod",
        "(closest: `parse_mode`)",
    ),
    (
        "shortcuts/Mesage.toml",
        "[answer]\nhandwritten = true\n",
        ".",
        "no type `Mesage`",
    ),
    (
        "shortcuts/Message.toml",
        "[answer]\nmethod = \"sendMesage\"\n",
        "answer.method",
        "no method `sendMesage` (closest: `sendMessage`)",
    ),
    (
        "shortcuts/Message.toml",
        "[answer]\nmethod = \"sendMessage\"\n[answer.fill]\nchat = \"self.chat.id\"\n",
        "answer.fill.chat",
        "no param of method `sendMessage`: `chat`",
    ),
    (
        "shortcuts/Message.toml",
        "[answer]\nmethod = \"sendMessage\"\nignore = [\"reply_to\"]\n",
        "answer.ignore[0]",
        "no param of method `sendMessage`: `reply_to`",
    ),
    (
        "shortcuts/Message.toml",
        "[answer]\nignore = []\n",
        "answer",
        "needs `method`",
    ),
    (
        "shortcuts/Message.toml",
        "[answer]\nhandwritten = true\nmethod = \"sendMessage\"\n",
        "answer",
        "takes no `method` or `fill`",
    ),
    (
        "unions.toml",
        "[MaybeInacessibleMessage]\ntag = \"date\"\n",
        "MaybeInacessibleMessage",
        "no union `MaybeInacessibleMessage` (closest: `MaybeInaccessibleMessage`)",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\n",
        "MaybeInaccessibleMessage",
        "exactly one of `tag`, `rules`",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\ntag = \"text\"\n",
        "MaybeInaccessibleMessage.tag",
        "no field on type `InaccessibleMessage`: `text`",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\nrules = [{ member = \"Chat\", field = \"date\", eq = 0 }]\n",
        "MaybeInaccessibleMessage.rules[0].member",
        "no member `Chat`",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\nrules = [{ member = \"Message\", field = \"dat\", eq = 0 }]\n",
        "MaybeInaccessibleMessage.rules[0].field",
        "(closest: `date`)",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\nrules = [{ member = \"Message\", field = \"date\", eq = 0, absent = true }]\n",
        "MaybeInaccessibleMessage.rules[0]",
        "exactly one of `eq`, `ne`",
    ),
    (
        "unions.toml",
        "[MaybeInaccessibleMessage]\nrules = [{ member = \"Message\", field = \"date\" }]\n",
        "MaybeInaccessibleMessage.rules[0]",
        "exactly one of `eq`, `ne`",
    ),
    (
        "twins.toml",
        "[User]\nmerge = false\n",
        "User",
        "no type `InputUser`",
    ),
    (
        "twins.toml",
        "[ChatPermissions.required]\ncan_send = true\n",
        "ChatPermissions.required.can_send",
        "no field on type `ChatPermissions`: `can_send`",
    ),
    (
        "layout.toml",
        "[Message]\nhot = [\"message_id\", \"from_user\"]\n",
        "Message.hot[1]",
        "no field on type `Message`: `from_user`",
    ),
    (
        "layout.toml",
        "[Messages]\nfreelist = true\n",
        "Messages",
        "no type `Messages` (closest: `Message`)",
    ),
    (
        "heuristics.toml",
        "[returns]\ngetMee = { ref = \"User\" }\n",
        "returns.getMee",
        "no method `getMee` (closest: `getMe`)",
    ),
    (
        "heuristics.toml",
        "[returns]\ngetMe = { array = { union = [{ prim = \"int\" }, { ref = \"Usr\" }] } }\n",
        "returns.getMe",
        "no type, union or enum `Usr` (closest: `User`)",
    ),
    (
        "heuristics.toml",
        "[consts.Chat]\ntyp = \"private\"\n",
        "consts.Chat.typ",
        "(closest: `type`)",
    ),
    (
        "heuristics.toml",
        "[consts.Chats]\ntype = \"private\"\n",
        "consts.Chats",
        "no type `Chats`",
    ),
    (
        "heuristics.toml",
        "[subtypes]\nChatMembr = [\"User\"]\n",
        "subtypes.ChatMembr",
        "no union `ChatMembr` (closest: `ChatMember`)",
    ),
    (
        "heuristics.toml",
        "[subtypes]\nChatMember = [\"Usr\"]\n",
        "subtypes.ChatMember[0]",
        "no type `Usr`",
    ),
    (
        "heuristics.toml",
        "[enum_members]\nChatActon = [\"typing\"]\n",
        "enum_members.ChatActon",
        "no enum `ChatActon` (closest: `ChatAction`)",
    ),
    (
        "docs.toml",
        "[types.Mesage]\nnote = \"x\"\n",
        "types.Mesage",
        "no type `Mesage`",
    ),
    (
        "docs.toml",
        "[methods.getMee]\nnote = \"x\"\n",
        "methods.getMee",
        "no method `getMee`",
    ),
    (
        "methods.toml",
        "[idempotent]\ngetMee = true\n",
        "idempotent.getMee",
        "no method `getMee` (closest: `getMe`)",
    ),
    (
        "methods.toml",
        "excluded = [\"getUpdate\"]\n",
        "excluded[0]",
        "no method `getUpdate` (closest: `getUpdates`)",
    ),
    (
        "methods.toml",
        "excluded = [\"getUpdates\"]\n[idempotent]\ngetUpdates = true\n",
        "excluded[0]",
        "also in `idempotent`",
    ),
    (
        "display.toml",
        "[types]\nMessage = [\"date\"]\n",
        "types.Message[0]",
        "`Message.date` is not a string field",
    ),
    (
        "display.toml",
        "[methods]\nsendMessage = [\"message_thread_id\"]\n",
        "methods.sendMessage[0]",
        "`sendMessage.message_thread_id` is not a string param",
    ),
    (
        "display.toml",
        "[methods]\nsendMessag = [\"text\"]\n",
        "methods.sendMessag",
        "no method `sendMessag`",
    ),
    (
        "display.toml",
        "[methods]\nsendMessage = [\"txt\"]\n",
        "methods.sendMessage[0]",
        "(closest: `text`)",
    ),
    (
        "content.toml",
        "[[kind]]\nname = \"text\"\nfield = \"txt\"\n",
        "kind[0].field",
        "no field on type `Message`: `txt` (closest: `text`)",
    ),
    (
        "content.toml",
        "[[kind]]\nname = \"text\"\nfield = \"text\"\n[[kind]]\nname = \"text\"\nfield = \"caption\"\n",
        "kind[1].name",
        "duplicate content kind `text`",
    ),
    (
        "content.toml",
        "[[kind]]\nname = \"photo\"\nfield = \"photo\"\ncopy = { method = \"sendPhot\" }\n",
        "kind[0].copy.method",
        "no method `sendPhot` (closest: `sendPhoto`)",
    ),
    (
        "content.toml",
        "[[kind]]\nname = \"photo\"\nfield = \"photo\"\ncopy = { method = \"sendPhoto\", fill = { photos = \"self.photo\" } }\n",
        "kind[0].copy.fill.photos",
        "(closest: `photo`)",
    ),
    (
        "events.toml",
        "[mesage]\n",
        "mesage",
        "no update type `mesage` (closest: `message`)",
    ),
    (
        "events.toml",
        "[update_id]\n",
        "update_id",
        "no update type `update_id`",
    ),
    (
        "bases.toml",
        "ChatFullInfo = [\"MutableTelegramObject\"]\n",
        "ChatFullInfo[0]",
        "`MutableTelegramObject` is not allowed",
    ),
    (
        "bases.toml",
        "ChatFullInfo = [\"Chats\"]\n",
        "ChatFullInfo[0]",
        "no type `Chats` (closest: `Chat`)",
    ),
    (
        "bases.toml",
        "ChatFullInf = [\"Chat\"]\n",
        "ChatFullInf",
        "no type `ChatFullInf` (closest: `ChatFullInfo`)",
    ),
    (
        "errors.toml",
        "[names]\n\"Bad Request: message is not modifed\" = \"MESSAGE_NOT_MODIFIED\"\n",
        "names.\"Bad Request: message is not modifed\"",
        "(closest: `Bad Request: message is not modified`)",
    ),
    (
        "errors.toml",
        "[names]\n\"Bad Request: message is not modified\" = \"not_modified\"\n",
        "names.\"Bad Request: message is not modified\"",
        "UPPER_SNAKE_CASE",
    ),
    (
        "errors.toml",
        "[names]\n\"Bad Request: message is not modified\" = \"SAME\"\n\"Forbidden: bot was blocked by the user\" = \"SAME\"\n",
        "names.\"Forbidden: bot was blocked by the user\"",
        "`SAME` is also the name of `Bad Request: message is not modified`",
    ),
];

#[test]
fn a_dangling_reference_names_the_closest_ir_match() {
    let ir = ir();
    let mut failures = Vec::new();
    for (i, (file, text, at, fragment)) in DANGLING.iter().enumerate() {
        let mut files = with(file, text);
        if !VALID.iter().any(|(f, _)| f == file) {
            files.push((file, (*text).to_owned()));
        }
        let overlay = load(&format!("dangling-{i}"), &files).unwrap();
        let errors = overlay.check(&ir);
        let found = errors.iter().map(parts).any(|(name, got_at, message)| {
            Path::new(file).file_name().unwrap().to_string_lossy() == name
                && got_at == *at
                && message.contains(fragment)
        });
        if !found {
            let all: Vec<String> = errors.iter().map(Error::to_string).collect();
            failures.push(format!(
                "{file}: want `{at}: ...{fragment}...`, got {all:#?}"
            ));
        }
    }
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}

#[test]
fn errors_are_sorted_and_all_reported() {
    let mut files = with("events.toml", "[nope]\n");
    let datetime = "[types]\nMessage = [\"b_bad\", \"a_bad\"]\nChat = [\"zzz\"]\n";
    files.retain(|(f, _)| *f != "datetime.toml");
    files.push(("datetime.toml", datetime.to_owned()));
    let errors = load("sorted", &files).unwrap().check(&ir());
    let keys: Vec<(String, String)> = errors.iter().map(parts).map(|(f, at, _)| (f, at)).collect();
    let want = [
        ("datetime.toml", "types.Chat[0]"),
        ("datetime.toml", "types.Message[0]"),
        ("datetime.toml", "types.Message[1]"),
        ("events.toml", "nope"),
    ];
    let want: Vec<(String, String)> = want
        .iter()
        .map(|(f, a)| ((*f).to_owned(), (*a).to_owned()))
        .collect();
    assert_eq!(keys, want);
}

#[test]
fn error_pins_are_not_checked_without_errors_json() {
    let files = with("errors.toml", "[names]\n\"Bad Request: gone\" = \"GONE\"\n");
    let overlay = load("no-errors-source", &files).unwrap();
    let mut ir = ir();
    assert!(!overlay.check(&ir).is_empty());
    ir.header.sources.retain(|s| *s != Source::Errors);
    ir.errors.clear();
    assert!(overlay.check(&ir).is_empty());
    // the name rules still apply
    let files = with("errors.toml", "[names]\n\"Bad Request: gone\" = \"gone\"\n");
    let errors = load("no-errors-source-name", &files).unwrap().check(&ir);
    assert_eq!(errors.len(), 1, "{errors:?}");
}

#[test]
fn events_without_an_update_type_reject_every_entry() {
    let mut ir = ir();
    ir.types.retain(|t| t.name != "Update");
    let errors = Overlay::load(&scratch("no-update", VALID))
        .unwrap()
        .check(&ir);
    let at: Vec<String> = errors.iter().map(parts).map(|(_, at, _)| at).collect();
    assert!(
        at.contains(&"message".to_owned()) && at.contains(&"edited_message".to_owned()),
        "{at:?}"
    );
}

#[test]
fn content_needs_a_message_type() {
    let mut ir = ir();
    ir.types.retain(|t| t.name != "Message");
    let errors = Overlay::load(&scratch("no-message", VALID))
        .unwrap()
        .check(&ir);
    assert!(
        errors
            .iter()
            .map(parts)
            .any(|(f, at, m)| f == "content.toml"
                && at == "kind[0].field"
                && m.contains("no type `Message`"))
    );
}

fn digest_of(name: &str, files: &[(&str, &str)]) -> String {
    overlay::digest(&scratch(name, files)).unwrap()
}

/// `VALID` with one file's path and text mapped.
fn mapped(
    f: impl Fn(&'static str, &'static str) -> (&'static str, &'static str),
) -> Vec<(&'static str, &'static str)> {
    VALID.iter().map(|(p, t)| f(p, t)).collect()
}

#[test]
fn digest_is_stable_and_sees_every_byte_and_rename() {
    let a = digest_of("digest-a", VALID);
    assert_eq!(
        a,
        digest_of("digest-b", VALID),
        "same content, another directory"
    );
    assert_eq!(a.len(), 64);
    // one byte more in one file
    let byte = mapped(|p, t| {
        (
            p,
            if p == "bases.toml" {
                "ChatFullInfo = [\"Chat\"]\n\n"
            } else {
                t
            },
        )
    });
    assert_ne!(a, digest_of("digest-byte", &byte));
    // the same bytes under another file name
    let renamed = mapped(|p, t| {
        (
            if p == "enums/ChatType.toml" {
                "enums/ChatKind.toml"
            } else {
                p
            },
            t,
        )
    });
    assert_ne!(a, digest_of("digest-rename", &renamed));
    // README.md is docs, not overlay data
    let readme = mapped(|p, t| (p, if p == "README.md" { "changed\n" } else { t }));
    assert_eq!(a, digest_of("digest-readme", &readme));
}

#[test]
fn digest_of_an_empty_overlay_is_the_empty_hash() {
    assert_eq!(
        overlay::digest(&scratch("digest-empty", &[])).unwrap(),
        butcher::fetch::sha256(b"")
    );
}

#[test]
fn an_unreadable_kind_file_is_an_io_error() {
    let dir = scratch("unreadable", &[]);
    std::fs::create_dir_all(dir.join("names.toml")).unwrap();
    assert!(matches!(Overlay::load(&dir), Err(Error::Io { .. })));
}
