# Overlay

Hand-written facts on top of the IR (v4/research/02 §3), loaded by `crates/butcher/src/overlay/` (plan C-06).

- **Strict.** An unknown key fails with `<file>: <key.path>: unknown field ...`. A file outside the layout below is
  an error too. Dot-files (`.DS_Store`, editor swap files) are ignored.
- **Checked against the IR.** Every type, field, method, param, union, enum, update type and `errors.json` message an
  entry names must exist. The error names the file, the key path and the closest IR name.
- **Absence is not an error here.** A missing file is an empty kind. Rules like "every method has an `idempotent`
  decision" belong to `butcher check` (C-23).
- **Names.** Keys are wire names (`from`, `sendMessage`). A fill value is fill-DSL text, either a string or
  `{ expr = "...", when = "..." }`. The loader stores it unparsed; `dsl::apply` resolves it (see *Fill-DSL* below).
- **Digest.** The manifest's `overlay_sha256` hashes every `*.toml` here, sorted by relative path; this README is not
  part of it.

## Layout

One file per kind. Enums and shortcuts get one file per entity, so a Bot API bump diff stays reviewable:

```
names.toml  datetime.toml  defaults.toml  unions.toml  twins.toml  layout.toml  heuristics.toml
docs.toml  methods.toml  display.toml  content.toml  events.toml  bases.toml  errors.toml
enums/<Name>.toml  shortcuts/<Type>.toml
```

## Kinds

**1. `names.toml`: Python names.** Python names for fields and params: aliases, keyword-safe names, and renames for
collisions with reserved names (D109). After the renames, no two fields of a type (params of a method) may share a
Python name. It also holds the Python alias of an inline union param.

```toml
[types.Message]
from = "from_user"
[types.ManagedBotCreated]
bot = "bot_user"
[union_aliases.sendMediaGroup]
media = "MediaUnion"
```

**2. `enums/<Name>.toml`: named enums.** The file stem is the enum name. Each file has at least one of four rules,
and rules combine:
- `parse`: a regexp over one field's or param's description; give exactly one of `type` / `method`;
- `multi_parse`: one value per type;
- `static`: fixed members;
- `extract`: one member per field name, so `UpdateType` comes from `Update`.

```toml
doc = "Type of chat"
[parse]
type = "Chat"
field = "type"
regexp = "'([a-z]+)'"
[static]
SENDER = "sender"
```

**3. `datetime.toml`: datetime fields.** Unix-time fields and params, returned as `datetime`; an explicit list.
Each entry must be an integer field or param.

```toml
[types]
Message = ["date", "edit_date"]
[methods]
banChatMember = ["until_date"]
```

**4. `defaults.toml`: bot-level defaults.** The bot-level `Default(...)` name for a field or param.

```toml
[methods.sendMessage]
parse_mode = "parse_mode"
[types.InputTextMessageContent]
parse_mode = "parse_mode"
```

**5. `shortcuts/<Type>.toml`: shortcuts.** One table per shortcut on the type; the table name is the Python method
name:
- `method`: the target method;
- `fill`: param → fill text, where every key is a param of `method`;
- `require` / `forbid`: guards, meaning `<path> is not None` / `<path> is None`, each with a message;
- `ignore`: params that are never forwarded (never also in `fill`);
- `handwritten = true`: the shortcut lives in `<type>_ext.rs` (D11) and takes no other key.

```toml
[answer]
method = "sendMessage"
require = [{ path = "self.chat", message = "This method can be used only if chat is present in the message." }]
ignore = ["reply_to_message_id"]
[answer.fill]
chat_id = "self.chat.id"
message_thread_id = { expr = "self.message_thread_id", when = "self.is_topic_message" }
direct_messages_topic_id = "self.direct_messages_topic?.topic_id"
reply_parameters = "self.as_reply_parameters()"
```

*Fill-DSL* (`crates/butcher/src/dsl.rs`), resolved for shortcut fills and guards and for `events.toml` (the
`content.toml` `copy.fill` text is not resolved yet; C-20 owns `send_copy`):
```text
expr  := path | "self." ident "()" | "None"
when  := path                        (truthiness; false omits the param)
path  := "self." ident (("." | "?.") ident)*
```
- Names are **Python** names, after the `names.toml` renames: `self.from_user`, not `self.from`. No whitespace, no
  other literal; a guard path takes no `?.`.
- Every step must be a field of the type (or, through a union, of every member; `?.` also accepts a field some
  members lack and gives `None` for the others).
- A step after an optional field needs `?.` or an earlier `require` guard on that exact path.
- The value must be assignable to the param: integer widths mix, `True` fits `Boolean`, a member fits its union.
  A value that may be `None` (optional, `?.`, a `when`, `None`) cannot fill a required param.
- `self.<helper>()` is a hand-written zero-argument helper declared for the type (`*_ext.pyi`); it never returns
  `None`.
- A `forbid` path must be able to be `None`, and an ignored param must be optional.
- A failed guard raises `ShortcutUnavailableError(AiogramError, ValueError)` with its message, raised explicitly so
  `python -O` keeps it (C-20).

**6. `unions.toml`: decoding undiscriminated unions.** How an undiscriminated union is decoded (D85, D107). Each
union gets exactly one of two forms:
- `tag`: a field on every member;
- `rules`: tried in order, each with exactly one of `eq`, `ne`, `present = true`, `absent = true`. When no rule
  matches, the value decodes as `Unknown`. There is no declaration-order fallback.

```toml
[MaybeInaccessibleMessage]
rules = [
  { member = "InaccessibleMessage", field = "date", eq = 0 },
  { member = "Message", field = "date", ne = 0 },
]
```

**7. `twins.toml`: twin merge overrides.** Overrides for the computed `Input*` twin merge (D18), keyed by the
documented type. `merge = false` keeps the two classes separate. `required` overrides the merged requiredness of a
field.

```toml
[ChatPermissions.required]
can_send_messages = false
```

**8. `layout.toml`: sparse layout.** The hot fields of the sparse layout (01 §3.1), and `freelist` for small
high-churn types.

```toml
[Message]
hot = ["message_id", "date", "chat", "from", "text", "entities"]
[MessageEntity]
freelist = true
```

**9. `heuristics.toml`: heuristic pins.** Pins for facts the HTML heuristics infer in html-only releases: return
types (in the IR `TypeRef` form), constants, union members, enum members.

```toml
[returns]
getChatAdministrators = { array = { ref = "ChatMember" } }
[consts.BotCommandScopeDefault]
type = "default"
[subtypes]
ChatMember = ["ChatMemberOwner", "ChatMemberAdministrator"]
[enum_members]
ChatType = ["private", "group"]
```

**10. `docs.toml`: docstring notes.** An RST note appended to a type's or method's docstring.

```toml
[types.Message]
note = "Use :meth:`answer` to reply in the same chat."
```

**11. `methods.toml`: idempotency.** The explicit `idempotent` decision per method (R19, PD-25). `excluded` lists
methods that are never retried at all; a method can't be in both.

```toml
excluded = ["getUpdates"]
[idempotent]
getMe = true
sendMessage = false
```

**12. `display.toml`: lazy display fields.** Display-text fields and params that accept lazy text (06 §3). Each entry
must be able to hold a string.

```toml
[types]
InlineKeyboardButton = ["text"]
[methods]
sendMessage = ["text"]
```

**13 + 14. `content.toml`: content kinds.** Message content kinds, in the 3.x `content_type` match order. Each kind
has:
- `name`: the routing value;
- `field`: the `Message` field that signals it;
- optional `copy`: the `send_copy` mapping, i.e. a method plus fill text per param.

```toml
[[kind]]
name = "photo"
field = "photo"
[kind.copy]
method = "sendPhoto"
[kind.copy.fill]
photo = "self.photo[-1].file_id"
caption = "self.caption"
```

**15. `events.toml`: event context.** Event-context paths per update type: `user`, `chat`, `thread_id`,
`business_connection_id`, each as fill text on the update's type (a `User`, a `Chat`, an integer, a string). An
empty table is a valid entry.

```toml
[message]
user = "self.from_user"
chat = "self.chat"
thread_id = { expr = "self.message_thread_id", when = "self.is_topic_message" }
[poll]
```

**16. `bases.toml`: secondary bases.** Secondary bases of a type (D83), as IR type names. `MutableTelegramObject` is
rejected (D15).

```toml
ChatFullInfo = ["Chat"]
```

**17. `errors.toml`: `ErrorReason` names.** `ErrorReason` member names keyed by the `errors.json` message (PD-24).
This one map holds both the pins written after first emission and the hand-written stable names. The messages are
not checked when the build has no `errors.json`.

```toml
[names]
"Bad Request: message is not modified" = "MESSAGE_NOT_MODIFIED"
"Forbidden: bot was blocked by the user" = "BOT_BLOCKED"
```
