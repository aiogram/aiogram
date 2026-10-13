## Why

A send with `ephemeral_message_parameters` lands in the chat's shared history with an
ordinary `message_id`. Telegram returns `message_id=0`, an `ephemeral_message_id` and the
`receiver_user`, and shows the message to the receiver only. Bot API 10.3 builds on that
shape:

- the `Message.reply_*` shortcuts make a reply to an ephemeral command ephemeral
  automatically;
- the `edit_ephemeral_*` and `delete_ephemeral` shortcuts need `receiver_user` to be set.

None of these paths can be exercised today. An actor cannot send an ephemeral command, an
ephemeral reply has nowhere to live, and the `editEphemeralMessage*` /
`deleteEphemeralMessage` family is record-only.

## What Changes

- **Outgoing ephemeral messages have Telegram's shape and their own store.** A send with
  `ephemeral_message_parameters` returns `message_id=0`, an `ephemeral_message_id` and
  `receiver_user`. The message is kept per chat and per receiver, outside the shared
  history, so the chat's messages and waits on them do not see it. It is only allowed in a
  group or supergroup, and only to a member of that chat.
- **Ephemeral messages are clickable by their receiver.** The receiver's `click()` finds
  buttons on ephemeral messages addressed to it. Another member's click fails, and the
  failure names the receiver.
- **The ephemeral edit and delete family is modeled.** `editEphemeralMessageText`,
  `...Caption`, `...Media`, `...ReplyMarkup` and `deleteEphemeralMessage` act on the store
  and reject a target that does not exist. They move off the record-only list.
- **An actor can send an ephemeral command.** `send(..., ephemeral=True)` delivers a
  message with `message_id=0` and an `ephemeral_message_id`. A reply that names it must
  itself be ephemeral and must name a message that exists, so `message.reply(...)` on such
  a command works as it does in production.

No API breaks. Observable behavior changes in one place: an ephemeral send no longer
appears in `chat.messages`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains four requirements, covering the ephemeral store and its
  addressing, receiver-only clicks, the modeled edit and delete family, and ephemeral
  commands from actors. No existing requirement text changes. The record-only list itself
  is code and docs, not spec text.

## Impact

- **Code**: `aiogram/test/world.py` (per-chat ephemeral store), `aiogram/test/modeling.py`
  (the ephemeral send path, reply validation, the edit and delete handlers,
  `RECORD_ONLY`), and `aiogram/test/actors.py` (`send(ephemeral=...)`, button search over
  ephemeral messages). No generated code changes.
- **Tests**: `tests/test_testing/` covers the store, sends, clicks, edits, deletes and
  commands. `test_record_only.py` follows the list change.
- **Docs**: an "Ephemeral messages" section in `docs/dispatcher/testing.rst`, and the
  record-only table updated.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
- **Order**: after `model-rich-message-content`, whose rich conversion
  `editEphemeralMessageText(rich_message=...)` reuses. `add-controllable-world-time` adds
  the 15-second reply window on top of this change.
