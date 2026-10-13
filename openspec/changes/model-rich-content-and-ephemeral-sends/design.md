## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- Sends go through one modeled handler and `build_message`. A payload field such as
  `rich_message` is synthesized, and then `_carry_request_values` overwrites it with the
  request's values. That overwrite runs one level deep and only where the annotations
  agree. `InputRichMessage.blocks` (`list[InputRichBlockUnion]`) never agrees with
  `RichMessage.blocks` (`list[RichBlockUnion]`), so nothing is carried and the
  synthesizer's empty list wins.
- `handle_edit_text` writes `text`, `entities` and `reply_markup`, so an edit that only
  carries `rich_message` clears the text and drops the content.
- `UserActor._iter_buttons` walks `reply_markup.inline_keyboard`. Every button lookup goes
  through it: `click`, the misdirected-click hint, and deep-link button following.
- `ChatState.messages` is the shared history. It is kept sorted by id, and the wait
  helpers, ordering guarantees and failure listings all read it.
- `RECORD_ONLY` in `modeling.py` lists `editEphemeralMessage*` and
  `deleteEphemeralMessage`. A guard test asserts it does not overlap with the registry.
- Ephemeral messages are addressed by chat, receiver and ephemeral id, which is how every
  `editEphemeralMessage*` and `deleteEphemeralMessage` call names its target.

## Goals / Non-Goals

**Goals:**

- No hand-kept list of rich block types anywhere in the toolkit. The next Bot API bump that
  adds a block type or a container should need no toolkit change, as with updates and
  administrator rights today.
- Ephemeral state never leaks into anything that reads the shared history.

**Non-Goals:**

- Resolving `InputRichMessage.media`, media that rich text references through
  `tg://photo?id=`-style links. Those links stay in the text as given.
- Parsing `html` or `markdown` rich input into blocks. That is Telegram's renderer, and a
  partial copy would produce content Telegram would not.
- The 15-second window for replying to an ephemeral message. The world clock is
  synthetic, so a test cannot honestly control "15 seconds later".
- How `replace_callback_query_message` looks. The ephemeral message is stored and the
  original message is left untouched; how a client renders the replacement is not world
  state.
- Waiting helpers for ephemeral messages. Tests read the store back directly.
- Expiry of ephemeral messages, and reuse of their ids.

## Decisions

### D1. Rich content is converted by reflection, not by a block table

An `InputRich*` model converts to the stored model whose name is the same minus the
`Input` prefix, resolved from `aiogram.types`. Fields are matched by name:

- a value whose type the target annotation accepts is carried;
- a nested `InputRich*` model, or a list of them, is converted recursively;
- anything else is left to the synthesizer. That covers media (`InputMediaPhoto` becomes
  `list[PhotoSize]`) and the target's required fields the input lacks (`label`, a map's
  dimensions).

The target starts as a synthesized instance and the converted fields are applied over it,
so every required field always has a value. This is `_carry_request_values` applied
recursively, and it reuses the same `annotation_accepts`.

Rich text (`RichTextUnion`, including `RichTextButton`) is shared between input and
output, so it is carried as-is.

*Alternative considered:* a dict from each `InputRichBlock*` to a converter function. It
would read more explicitly, but 26 block types would need updating on every bump. A new
block type with no entry would be dropped silently, which is the bug being fixed.

### D2. Buttons are found by walking the model tree

`_iter_buttons` yields every `InlineKeyboardButton` and every `RichMessageButton` it finds
by walking the message's `reply_markup` and `rich_message` as pydantic model trees. It
does not know which blocks hold buttons, for the same reason as D1. Callers only read
`callback_data` and `url`, which both button types carry, so `click`, the hint and
deep-link following gain rich buttons with no change of their own.

*Alternative considered:* a typed walk over `RichBlockButtons` and `RichTextButton`. Rich
text nests through bold, italic, links, list items, details and table cells, so a typed
walk is the hand-kept list again.

### D3. Ephemeral messages live in a per-chat store, not in `messages`

`ChatState` gains a store keyed by `(receiver_id, ephemeral_message_id)`, and reads it
through `chat.ephemeral_messages(user)`, in send order. Ids come from a per-chat counter
that is separate from `last_message_id`. Telegram allows ids to be reused after expiry, so
never reusing one is a valid subset of its behavior. A stored message goes through the
same binding as `add_message`, so shortcuts work on it.

Incoming ephemeral commands go into the same store under their sender's id, with no
`receiver_user`. The Bot API defines `receiver_user` only as the user who received an
ephemeral message, and the receiver of a user's command is the bot. Reply validation
(D5) finds the command there.

*Alternative considered:* storing ephemeral messages in `messages` with a flag. Every
reader of the shared history (waits, `messages[-1]`, failure listings, ordering by id with
`message_id=0`) would need to filter, and forgetting to filter is exactly the bug.

### D4. The ephemeral path is chosen by the request, not by the method

Any send whose request carries `ephemeral_message_parameters` takes the ephemeral path in
`build_message`. That is decided by attribute, not by a list of send methods, so the 14
methods that declare the field, and any future one, behave the same. The path:

- checks that the chat is a group or supergroup;
- checks that the receiver is a member;
- builds the message with `message_id=0`, a fresh `ephemeral_message_id` and
  `receiver_user`;
- stores it per D3 and returns it.

Rejections use `ApiRejection`, so the bot sees `TelegramBadRequest` as in production.

### D5. Replies to ephemeral messages are validated where Telegram documents a rule

When `reply_parameters.ephemeral_message_id` is set:

- the request must carry `ephemeral_message_parameters` ("a reply to an ephemeral message
  must itself be an ephemeral message");
- the id must name an incoming ephemeral message in that chat.

The receiver is not required to equal the command's sender. The Bot API does not state
that rule, and the `reply_*` shortcuts set it that way anyway.

### D6. The ephemeral edit and delete family is modeled and leaves `RECORD_ONLY`

`editEphemeralMessageText`, `...Caption`, `...Media` and `...ReplyMarkup` update the
stored message through the same `derive_message` the regular edits use.
`editEphemeralMessageText` takes `rich_message` through D1. `deleteEphemeralMessage`
removes the message. A target missing for that chat and receiver fails with Telegram's
regular wording, "message to edit not found" or "message to delete not found". Each method
returns `True`, as its schema declares. The five methods move from `RECORD_ONLY` to the
registry in the same change, which the guard test requires. `sendMessageDraft` and
`sendRichMessageDraft` stay record-only.

### D7. A click on someone else's ephemeral button names the receiver

The actor's button search covers the shared history and the ephemeral messages addressed
to it. When that misses, the misdirected-click hint also looks at ephemeral messages
addressed to other users in the same chat, and names the receiver. This follows the
toolkit's existing rule that a setup mistake must not read like a typo.

### D8. `send(ephemeral=True)` is an explicit flag

The actor marks a command as ephemeral explicitly. It does not infer that from the bot's
registered commands (`BotCommand.is_ephemeral`). The registered list is per scope and per
language, and a test that wants an ephemeral message should say so. An ephemeral send is
refused, with `WorldLookupError` (a setup error), outside a group or supergroup, and when
combined with a business binding.

## Risks / Trade-offs

- [Error wording for "ephemeral outside a group" and "receiver is not a member" is not
  documented by Telegram] → The toolkit's own `Bad Request: ...` wording is used, in one
  place each. Tests should assert the exception type, not the text.
- [D1 relies on the `Input` prefix naming convention] → It holds for every model
  reachable from `InputRichMessage.blocks` in the current schema. A guard test walks that
  graph and asserts that each model has a counterpart, so a bump that breaks the
  convention fails loudly instead of dropping content. `InputRichMessageContent` (inline
  results) and `InputRichMessageMedia` have no counterpart, and neither is reachable from
  `blocks`.
- [Walking model trees (D2) on every click costs more than walking a keyboard] → Messages
  in tests are small, and the walk stops at leaves. Not measurable at test scale.
- [Behavior a test observed changes: rich messages gain blocks, ephemeral sends leave
  `chat.messages`] → Both old behaviors were wrong, and the toolkit has not been released.
  The changelog fragment states it.

## Migration Plan

None at runtime. Tests that read an ephemeral send from `chat.messages` switch to
`chat.ephemeral_messages(user)`.

## Open Questions

- Should `chat.ephemeral_messages()` with no user return every receiver's messages? This
  is deferrable: the per-user form covers the specified scenarios, and adding a default
  later is backward compatible.
