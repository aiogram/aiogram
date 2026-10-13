## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- Sends go through one modeled handler and `build_message`, which stores every message in
  `ChatState.messages`, the shared history. That history is kept sorted by id, and the
  wait helpers, ordering guarantees and failure listings all read it.
- `RECORD_ONLY` in `modeling.py` lists `editEphemeralMessage*` and
  `deleteEphemeralMessage`. A guard test asserts it does not overlap with the registry.
- Ephemeral messages are addressed by chat, receiver and ephemeral id, which is how every
  `editEphemeralMessage*` and `deleteEphemeralMessage` call names its target. The
  generated `Message.edit_ephemeral_*` and `delete_ephemeral` shortcuts read `chat`,
  `receiver_user` and `ephemeral_message_id` off the message.
- `UserActor._iter_buttons` is the single place button lookups go through. After
  `model-rich-message-content` it walks rich content as well.

## Goals / Non-Goals

**Goals:**

- Ephemeral state never leaks into anything that reads the shared history.

**Non-Goals:**

- The 15-second window for replying to an ephemeral message. It needs a controllable
  clock, which `add-controllable-world-time` introduces, and that change specifies the
  window.
- How `replace_callback_query_message` looks. The ephemeral message is stored and the
  original message is left untouched; how a client renders the replacement is not world
  state.
- Waiting helpers for ephemeral messages. Tests read the store back directly.
- Expiry of ephemeral messages, and reuse of their ids. Neither is documented.

## Decisions

### D1. Ephemeral messages live in a per-chat store, not in `messages`

`ChatState` gains a store keyed by `(receiver_id, ephemeral_message_id)`, and reads it
through `chat.ephemeral_messages(user)`, in send order. Ids come from a per-chat counter
that is separate from `last_message_id`. Telegram allows ids to be reused after expiry, so
never reusing one is a valid subset of its behavior. A stored message goes through the
same binding as `add_message`, so shortcuts work on it.

Incoming ephemeral commands go into the same store under their sender's id, with no
`receiver_user`. The Bot API defines `receiver_user` only as the user who received an
ephemeral message, and the receiver of a user's command is the bot. Reply validation
(D3) finds the command there.

*Alternative considered:* storing ephemeral messages in `messages` with a flag. Every
reader of the shared history (waits, `messages[-1]`, failure listings, ordering by id with
`message_id=0`) would need to filter, and forgetting to filter is exactly the bug.

### D2. The ephemeral path is chosen by the request, not by the method

Any send whose request carries `ephemeral_message_parameters` takes the ephemeral path in
`build_message`. That is decided by attribute, not by a list of send methods, so the 14
methods that declare the field, and any future one, behave the same. The path:

- checks that the chat is a group or supergroup;
- checks that the receiver is a member;
- builds the message with `message_id=0`, a fresh `ephemeral_message_id` and
  `receiver_user`;
- stores it per D1 and returns it.

Rejections use `ApiRejection`, so the bot sees `TelegramBadRequest` as in production.

### D3. Replies to ephemeral messages are validated where Telegram documents a rule

When `reply_parameters.ephemeral_message_id` is set:

- the request must carry `ephemeral_message_parameters` ("a reply to an ephemeral message
  must itself be an ephemeral message");
- the id must name an incoming ephemeral message in that chat.

The receiver is not required to equal the command's sender. The Bot API does not state
that rule, and the `reply_*` shortcuts set it that way anyway.

### D4. The ephemeral edit and delete family is modeled and leaves `RECORD_ONLY`

`editEphemeralMessageText`, `...Caption`, `...Media` and `...ReplyMarkup` update the
stored message through the same `derive_message` the regular edits use.
`editEphemeralMessageText` converts `rich_message` with the conversion from
`model-rich-message-content`. `deleteEphemeralMessage` removes the message. A target
missing for that chat and receiver fails with Telegram's regular wording, "message to edit
not found" or "message to delete not found". Each method returns `True`, as its schema
declares. The five methods move from `RECORD_ONLY` to the registry in the same change,
which the guard test requires. `sendMessageDraft` and `sendRichMessageDraft` stay
record-only.

### D5. A click on someone else's ephemeral button names the receiver

The actor's button search covers the shared history and the ephemeral messages addressed
to it. When that misses, the misdirected-click hint also looks at ephemeral messages
addressed to other users in the same chat, and names the receiver. This follows the
toolkit's existing rule that a setup mistake must not read like a typo.

### D6. `send(ephemeral=True)` is an explicit flag

The actor marks a command as ephemeral explicitly. It does not infer that from the bot's
registered commands (`BotCommand.is_ephemeral`). The registered list is per scope and per
language, and a test that wants an ephemeral message should say so. An ephemeral send is
refused, with `WorldLookupError` (a setup error), outside a group or supergroup, and when
combined with a business binding.

## Risks / Trade-offs

- [Error wording for "ephemeral outside a group" and "receiver is not a member" is not
  documented by Telegram] → The toolkit's own `Bad Request: ...` wording is used, in one
  place each. Tests should assert the exception type, not the text.
- [Telegram does not document whether an incoming ephemeral command carries
  `receiver_user`] → It is left unset (D1). If Telegram turns out to set it, adding it is
  backward compatible for tests.
- [A test that read an ephemeral send from `chat.messages` stops finding it] → The old
  behavior was wrong, and the toolkit has not been released. The changelog fragment states
  it.

## Migration Plan

None at runtime. Tests that read an ephemeral send from `chat.messages` switch to
`chat.ephemeral_messages(user)`.

## Open Questions

- Should `chat.ephemeral_messages()` with no user return every receiver's messages? This
  is deferrable: the per-user form covers the specified scenarios, and adding a default
  later is backward compatible.
