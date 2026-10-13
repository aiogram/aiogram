## Why

Bot API 10.3 put interactive content in two places `aiogram.test` does not model, so a bot
using either cannot be tested end to end.

**Rich messages lose their content.** `sendRichMessage` stores a message whose
`rich_message` is a synthesized empty `RichMessage(blocks=[])`: the blocks the bot sent are
dropped. This predates 10.3, but 10.3 added buttons inside rich blocks (`RichBlockButtons`,
`RichTextButton`). A bot that sends a callback button that way gets
`WorldLookupError: No message ... carries a button`. The spec already promises that a
button on a rich message is clickable. `editMessageText(rich_message=...)` has the same
gap, and also clears the stored text.

**Ephemeral messages are stored as public ones.** A send with
`ephemeral_message_parameters` lands in the chat's shared history with an ordinary
`message_id`. Telegram returns `message_id=0`, an `ephemeral_message_id` and the
`receiver_user`. 10.3's `Message.reply_*` shortcuts make a reply to an ephemeral command
ephemeral automatically, and the `edit_ephemeral_*` / `delete_ephemeral` shortcuts need
`receiver_user` to be set. None of these paths can be exercised today: an actor cannot
send an ephemeral command, an ephemeral reply has nowhere to live, and the
`editEphemeralMessage*` / `deleteEphemeralMessage` family is record-only.

## What Changes

- **Rich content is carried, not synthesized.** A sent or edited rich message stores the
  blocks its request stated, converted from the `InputRichBlock*` shapes to the
  `RichBlock*` shapes Telegram returns. Media inside blocks is synthesized, as it already is
  for `sendPhoto` and its siblings. A required field the input does not carry (a list
  item's `label`, a map's dimensions) is synthesized. `html` and `markdown` input is not
  parsed into blocks; that limitation is documented.
- **`editMessageText(rich_message=...)` replaces the stored rich content** instead of
  clearing the message's text.
- **`click()` finds callback buttons inside rich content**, at any nesting depth, as well
  as in `reply_markup`. The misdirected-click hint covers them too.
- **Outgoing ephemeral messages have Telegram's shape and their own store.** A send with
  `ephemeral_message_parameters` returns `message_id=0`, an `ephemeral_message_id` and
  `receiver_user`. The message is kept per chat and per receiver, outside the shared
  history, so the chat's messages and waits on them do not see it. It is only allowed in a
  group or supergroup, and only to a member of that chat.
- **Ephemeral messages are clickable by their receiver.** The receiver's `click()` finds
  buttons on ephemeral messages addressed to it. The resulting `callback_query` carries the
  ephemeral message. Other members cannot reach those buttons.
- **The ephemeral edit and delete family is modeled.** `editEphemeralMessageText`,
  `...Caption`, `...Media`, `...ReplyMarkup` and `deleteEphemeralMessage` act on the store
  and reject a target that does not exist. They move off the record-only list.
- **An actor can send an ephemeral command.** `send(..., ephemeral=True)` delivers a
  message with `message_id=0` and an `ephemeral_message_id`. A reply that names it through
  `reply_parameters.ephemeral_message_id` must itself be ephemeral and must name a message
  that exists. `message.reply(...)` on such a command therefore works as it does in
  production.

None of these changes break an API. The behavior a test observes does change in two
places. A rich message now carries its blocks instead of an empty list. An ephemeral send
no longer appears in `chat.messages`. A test that asserted the old, incorrect behavior has
to change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains six requirements and modifies none. They cover rich
  content carried into stored messages, clickable buttons inside rich content, the
  ephemeral message store and its addressing, receiver-only clicks on ephemeral messages,
  the modeled ephemeral edit and delete family, and ephemeral commands from actors.
  Existing requirements keep their text. "A sent message carries the values its request
  stated" and "the record-only surface is an enumerated decision" stay true as written:
  the record-only list itself is code and docs, not spec text.

## Impact

- **Code**: `aiogram/test/modeling.py` (rich conversion; send, edit and ephemeral
  handlers; `RECORD_ONLY`), `aiogram/test/world.py` (per-chat ephemeral store),
  `aiogram/test/actors.py` (`send(ephemeral=...)`, button search over rich content and
  ephemeral messages). No generated code changes.
- **Tests**: `tests/test_testing/` gains coverage for rich conversion, clicks inside rich
  content, the ephemeral lifecycle and ephemeral commands. `test_record_only.py`
  follows the list change.
- **Docs**: `docs/dispatcher/testing.rst`, for rich content and its `html`/`markdown`
  limitation, a new ephemeral messages section, and the record-only table.
- **Changelog**: folded into `CHANGES/1887.feature.rst`, the toolkit's single fragment.
- **Risk**: the error wording for an ephemeral send outside a group, or to a non-member, is
  not documented by Telegram. The toolkit's own wording is used and the design marks it as
  such.
