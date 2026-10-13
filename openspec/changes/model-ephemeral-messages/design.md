## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- Sends go through one modeled handler and `build_message`, which stores every message in
  `ChatState.messages`, the shared history. That history is kept sorted by id, and the
  wait helpers, ordering guarantees and failure listings all read it.
- `BotTestEnvironment.feed` registers every incoming message carried by an update through
  `_register_carried_message`, keyed by `message_id`. It refuses a second, different
  message under an id already held. Two ephemeral commands, both with id 0, would collide
  there.
- `RECORD_ONLY` in `modeling.py` lists `editEphemeralMessage*` and
  `deleteEphemeralMessage`, with a comment saying Telegram does not persist them. A guard
  test asserts the list does not overlap with the registry.
- Ephemeral messages are addressed by chat, receiver and ephemeral id, which is how every
  `editEphemeralMessage*` and `deleteEphemeralMessage` call names its target. The aiogram
  shortcuts `Message.edit_ephemeral_*` and `delete_ephemeral` read `chat`, `receiver_user`
  and `ephemeral_message_id` off the message.
- For an incoming ephemeral message, aiogram's `Message.as_reply_parameters()` returns
  `ephemeral_message_id` with no `message_id`, and `as_ephemeral_message_parameters()`
  addresses the reply to `from_user`. So `message.reply()` builds a valid ephemeral reply
  without the toolkit's help, while `message.answer()` sends an ordinary shared message.
- `click(target, message=...)` uses the given message without checking that it is visible
  to the actor.
- Pending queries map an id to its kind. Nothing records which message a callback query
  came from. The world now records which callback queries came from an ephemeral message
  (`ephemeral_callbacks`), which is all D3's replace rule reads.

## Goals / Non-Goals

**Goals:**

- Ephemeral state never leaks into anything that reads the shared history.
- Rules are enforced only where the Bot API states them, and the source of each is named.

**Non-Goals:**

- The 15-second window for replying to an ephemeral message. It needs a controllable
  clock, which `add-controllable-world-time` introduces, and that change specifies the
  window.
- How `replace_callback_query_message` looks. A replacing ephemeral message is stored like
  any other, and the original message is left untouched; how a client renders the
  replacement is not world state.
- Waiting helpers for ephemeral messages. Tests read the stores back directly.
- When ephemeral messages expire, which is undocumented. Ids are never reused, which is a
  valid subset of "may be reused after the message is deleted or expires".
- A user editing or replying to an ephemeral message. Actor `edit` and `reply` refuse an
  ephemeral target with a setup error, rather than guessing at behavior the Bot API does
  not describe.
- Membership of the receiver. The Bot API does not state it as a condition, and the
  existing requirement "Permissions are stored but not enforced" keeps membership out of
  send validation. The only check is that the receiver is a user this world declares.

## Decisions

### D1. Two per-chat stores, one per direction

`ChatState` gains two stores, kept out of `messages`. The separation means `edit_ephemeral`
can never land on a user's own command, and reply validation can never accept the bot's
own message as the "incoming" one.

| Store | Holds | Keyed by | Read with |
|---|---|---|---|
| outgoing (`sent_ephemeral`) | what the bot sent | `(receiver_id, ephemeral_message_id)` | `chat.ephemeral_messages(user)` |
| incoming (`received_ephemeral`) | what users sent | `(sender_id, ephemeral_message_id)` | `chat.ephemeral_commands(user)` |

- Clicks, the receiver-naming hint, and the edit and delete family see the outgoing store
  only.
- Reply validation (D3) sees the incoming store only.
- Both stores draw ids from one per-chat counter, separate from `last_message_id`, so an
  id never names two messages in the same chat.
- A stored message goes through the same binding as `add_message`, so shortcuts work on
  it.
- An incoming message carries no `receiver_user`. `BotCommand.is_ephemeral` describes the
  message as "seen only by the sender of the message and the bot", and the Bot API defines
  `receiver_user` only for "the user who received the message".

*Alternative considered:* one store with a direction flag. Every reader would need to
filter, which is the same failure mode as flagging messages in `messages`.

### D2. Registration routes by `ephemeral_message_id`

`_register_carried_message` sends any carried message that has an `ephemeral_message_id`
to the incoming store, unless that id is already there, and skips the shared-history id
check for it. That holds whether the message came from `send(ephemeral=True)`, a `fields=`
override, or a hand-built update fed directly. `send(ephemeral=True)` stores the command
before feeding it, as `send` does for ordinary messages, so registration finds it already
there and does nothing.

### D3. The outgoing path is chosen by the request, not by the method

Any send whose request carries `ephemeral_message_parameters` takes the ephemeral path in
`build_message`. That is decided by attribute, not by a list of send methods, so the 14
methods that declare the field, and any future one, behave the same. The path:

1. Refuses a chat that is not a group or supergroup. The source is the deprecated
   `receiver_user_id` text, "for group and supergroup chats only", which the current
   `EphemeralMessageParameters` text does not repeat. This is the toolkit's reading, and
   Risks says so.
2. Resolves the receiver through the world. An undeclared user is a `WorldLookupError`
   (setup gap), as everywhere else.
3. If `reply_parameters.ephemeral_message_id` is set, requires that it names an entry in
   the incoming store, as `ReplyParameters` describes it: "the incoming ephemeral
   message". The ephemeral parameters are present by construction on this path.
4. If `callback_query_id` names a callback query whose message was ephemeral, refuses
   `replace_callback_query_message=True`, which the schema forbids. It does not consume
   the pending query: `answerCallbackQuery` is still owed.
5. Builds the message with `message_id=0`, a fresh `ephemeral_message_id`, `receiver_user`
   and the request's `message_thread_id`. A reply that names an ephemeral command carries
   no `reply_to_message`, which the Bot API says "may be omitted" for replies to ephemeral
   messages. A reply to a shared message keeps it, as any reply does. The message is
   stored in the outgoing store and returned.

A send without ephemeral parameters whose `reply_parameters.ephemeral_message_id` is set
is refused before the regular path ("a reply to an ephemeral message must itself be an
ephemeral message"). Rejections use `ApiRejection`, so the bot sees `TelegramBadRequest`.

### D4. The ephemeral edit and delete family is modeled and leaves `RECORD_ONLY`

`editEphemeralMessageText`, `...Caption`, `...Media` and `...ReplyMarkup` update the
stored message through the same `derive_message` the regular edits use.
`editEphemeralMessageText` converts `rich_message` with the conversion from
`model-rich-message-content`. `deleteEphemeralMessage` removes the message. A target
missing for that chat and receiver, including a matching id under another receiver, fails
with "message to edit not found" or "message to delete not found". Each method returns
`True`, as its schema declares. The five methods move from `RECORD_ONLY` to the registry,
and the list's comment is rewritten to cover the drafts only.

The regular `editMessage*` and `deleteMessage` look up `message_id=0` in the shared
history, find nothing, and fail as they already do. That is the specified behavior, with no
special case.

### D5. Click resolution for ephemeral messages

The actor's button search covers the outgoing messages addressed to it, newest first,
before the shared history. An ephemeral message is the more specific target, and the two
cannot be ordered by id (`message_id=0`). An explicit `message=` must be visible to the
actor: a shared message, or an ephemeral one addressed to it. Anything else fails like a
miss.

On a miss, the misdirected-click hint also searches outgoing messages addressed to other
users in the same chat and names the receiver. This extends the existing requirement "A
misdirected click names where the button actually is", which covers other chats today,
without changing its text.

The callback query records which message it came from, so D3's
`replace_callback_query_message` check can tell an ephemeral origin.

### D6. `send(ephemeral=True)` is an explicit flag

The actor marks a command as ephemeral explicitly. It does not infer that from the bot's
registered commands (`BotCommand.is_ephemeral`). The registered list is per scope and per
language, and a test that wants an ephemeral message should say so.

The trigger refuses with `WorldLookupError` (a setup error) outside a group or supergroup,
and when combined with a business binding. In a topic-bound actor the command carries the
topic's thread. The command is read back with `chat.ephemeral_commands(user)`, and the
`send` docstring, which points at `chat.messages[-1]`, says so.

## Risks / Trade-offs

- [The group-only rule comes from deprecated parameter text] → If Telegram allows
  ephemeral messages elsewhere, the toolkit refuses a valid call. The rule sits in one
  place, its source is cited in the code and the docs, and tests should assert the
  exception type.
- [Error wording for the group-only refusal, a late or invalid ephemeral reply, and the
  replace rule is not documented] → The toolkit's own `Bad Request: ...` wording is used,
  in one place each.
- [Telegram does not document whether an incoming ephemeral command carries
  `receiver_user`] → It is left unset (D1). If Telegram turns out to set it, adding it is
  backward compatible for tests.
- [A test that read an ephemeral send from `chat.messages` stops finding it] → The old
  behavior was wrong, and the toolkit is in alpha. The changelog fragment states it.

## Migration Plan

None at runtime. Tests that read an ephemeral send from `chat.messages` switch to
`chat.ephemeral_messages(user)`.

## Open Questions

- Should `chat.ephemeral_messages()` with no user return every receiver's messages? This
  is deferrable: the per-user form covers the specified scenarios, and adding a default
  later is backward compatible.
