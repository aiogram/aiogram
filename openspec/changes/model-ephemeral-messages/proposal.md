## Why

A send with `ephemeral_message_parameters` lands in the chat's shared history with an
ordinary `message_id`. Telegram returns `message_id=0`, an `ephemeral_message_id` and the
`receiver_user`, and shows the message to the receiver only. aiogram's own shortcuts build
on that shape:

- `Message.reply_*` makes a reply to an ephemeral command ephemeral automatically;
- `edit_ephemeral_*` and `delete_ephemeral` need `receiver_user` to be set.

None of these paths can be exercised today:

- an actor cannot send an ephemeral command, and a hand-fed one collides in the history
  with the next one, since both have `message_id=0`;
- an ephemeral reply has nowhere to live;
- the `editEphemeralMessage*` / `deleteEphemeralMessage` family is record-only;
- any member can click a button meant for one user.

## What Changes

- **Outgoing ephemeral messages have Telegram's shape and their own store.** A send with
  `ephemeral_message_parameters` returns `message_id=0`, an `ephemeral_message_id` and
  `receiver_user`. The message is kept per chat and per receiver, outside the shared
  history, so the chat's messages and waits on them do not see it. Sending one outside a
  group or supergroup is refused.
- **Ephemeral messages are clickable only by their receiver.** Another member's click fails,
  and the failure names the receiver. A callback query from an ephemeral message cannot be
  answered with a replacing ephemeral message, as the Bot API states.
- **The ephemeral edit and delete family is modeled.** `editEphemeralMessageText`,
  `...Caption`, `...Media`, `...ReplyMarkup` and `deleteEphemeralMessage` act on the store,
  and reject a target that does not exist for that receiver. They move off the record-only
  list. The regular edit and delete methods do not reach ephemeral messages.
- **An actor can send an ephemeral command.** `send(..., ephemeral=True)` delivers a message
  with `message_id=0` and an `ephemeral_message_id`, kept in its own store. A reply that
  names it must itself be ephemeral and must name an incoming message, so
  `message.reply(...)` on such a command works as it does in production.

No API breaks. Observable behavior changes in one place: an ephemeral send no longer
appears in `chat.messages`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains four requirements, covering the ephemeral stores and
  their addressing, receiver-only clicks, the modeled edit and delete family, and ephemeral
  commands from actors. No existing requirement text changes. The receiver-naming hint
  extends "A misdirected click names where the button actually is" without contradicting
  it. The record-only list itself is code and docs, not spec text.

## Impact

- **Code**:
  - `aiogram/test/world.py`: the per-chat ephemeral stores.
  - `aiogram/test/environment.py`: registration of carried ephemeral messages.
  - `aiogram/test/modeling.py`: the ephemeral send path, reply validation, the edit and
    delete handlers, `RECORD_ONLY` and its comment.
  - `aiogram/test/actors.py`: `send(ephemeral=...)`, button search and `click(message=...)`
    visibility, callback origin.

  No generated code changes.
- **Tests**: `tests/test_testing/` covers the stores, sends, clicks, edits, deletes and
  commands. `test_record_only.py` follows the list change.
- **Docs**: an "Ephemeral messages" section in `docs/dispatcher/testing.rst`, and the
  record-only table updated.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: after `model-rich-message-content`, whose rich conversion
  `editEphemeralMessageText(rich_message=...)` reuses. `add-controllable-world-time` adds
  the 15-second reply window on top of this change.
