# Tasks

## 1. Rich content is carried

- [ ] 1.1 Add a recursive `InputRich*` → `RichBlock*` conversion to `aiogram/test/modeling.py` per design D1 (synthesized base, carry by name where the annotation accepts, recurse into nested input models and lists, synthesize the rest), and use it for `sendRichMessage`; verify with tests that a sent paragraph/list/button block/table round-trips into the stored message, a photo block carries a schema-valid synthesized photo, a list item gets a synthesized `label`, and `html`/`markdown`-only input stores an empty block list
- [ ] 1.2 Add a guard test that walks every model reachable from `InputRichMessage.blocks` and asserts each has an `Input`-less counterpart in `aiogram.types`; verify it passes now and fails when pointed at a model without one
- [ ] 1.3 Make `editMessageText(rich_message=...)` replace the stored rich content through the same conversion without clearing other fields; verify with a test that edits a rich message and asserts the new blocks and an untouched `reply_markup`
- [ ] 1.4 Document rich content in `docs/dispatcher/testing.rst` (carried blocks, synthesized media, the `html`/`markdown` and `media` limitations); verify the docs build shows no new warnings for `testing.rst`

## 2. Buttons inside rich content are clickable

- [ ] 2.1 Rewrite `UserActor._iter_buttons` to walk `reply_markup` and `rich_message` as model trees and yield both `InlineKeyboardButton` and `RichMessageButton` (design D2); verify that clicking a callback button in a button block, and in a `RichTextButton` nested in a list item and in a details block, dispatches a `callback_query` with the stored rich message
- [ ] 2.2 Verify the misdirected-click hint and deep-link button following work on rich buttons, with tests for a rich button in another chat and for a rich `url` button carrying a start link
- [ ] 2.3 Note in `docs/dispatcher/testing.rst` that `click()` reaches buttons in rich content; verify the example in the docs matches a passing test

## 3. Outgoing ephemeral messages

- [ ] 3.1 Add the per-chat ephemeral store to `ChatState` (keyed by receiver and ephemeral id, own id counter, binding as `add_message` does) with `chat.ephemeral_messages(user)` accepting a spec, state or id (design D3); verify with world-level tests for ordering, id allocation and isolation from `chat.messages`
- [ ] 3.2 Route any send carrying `ephemeral_message_parameters` through an ephemeral path in `build_message` (design D4): group/supergroup only, receiver must be a member, `message_id=0`, `ephemeral_message_id`, `receiver_user`; verify with tests for the returned shape, absence from `chat.messages`, a `wait_for_message` that is not satisfied by it, and `TelegramBadRequest` with nothing stored for a non-member receiver and for a private chat and a channel
- [ ] 3.3 Verify a non-text send (`sendPhoto` with `ephemeral_message_parameters`) and `sendRichMessage` take the same path, with one test each
- [ ] 3.4 Add an "Ephemeral messages" section to `docs/dispatcher/testing.rst` covering the shape, the store and reading it back; verify the docs build shows no new warnings for `testing.rst`

## 4. Ephemeral clicks, edits and deletions

- [ ] 4.1 Extend the actor's button search to the ephemeral messages addressed to it, and the misdirected-click hint to name the receiver of another user's ephemeral message (design D7); verify that the receiver's click dispatches a `callback_query` whose `message` carries `ephemeral_message_id` and `receiver_user`, and that another member's click fails naming the receiver
- [ ] 4.2 Model `editEphemeralMessageText` (including `rich_message` via 1.1), `...Caption`, `...Media`, `...ReplyMarkup` and `deleteEphemeralMessage` against the store, returning `True` and rejecting a missing target with Telegram's regular wording (design D6); verify with a test per method, a test that a deleted message can no longer be edited, and a test that drives `message.edit_ephemeral_text()` and `message.delete_ephemeral()` shortcuts
- [ ] 4.3 Move those five methods from `RECORD_ONLY` to the registry and update the record-only table in `docs/dispatcher/testing.rst` (drafts stay); verify `tests/test_testing/test_record_only.py` passes

## 5. Ephemeral commands from actors

- [ ] 5.1 Add `ephemeral: bool = False` to `UserActor.send` producing `message_id=0` and an `ephemeral_message_id`, stored in the ephemeral store under the sender with no `receiver_user`, and refused with `WorldLookupError` outside a group/supergroup or with a business binding (design D3, D8); verify with tests for the dispatched shape, absence from `chat.messages` and both refusals
- [ ] 5.2 Validate `reply_parameters.ephemeral_message_id` on sends (design D5): the request must be ephemeral and the id must name an incoming ephemeral message in the chat; verify with tests that `message.reply(...)` to an ephemeral command produces an ephemeral reply to its sender, and that a non-ephemeral reply and a reply to an unknown id fail with `TelegramBadRequest` and store nothing
- [ ] 5.3 Document ephemeral commands in `docs/dispatcher/testing.rst` with a `send(..., ephemeral=True)` / `message.reply()` example; verify the example matches a passing test

## 6. Changelog, spec and integration

- [ ] 6.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the two observable behavior changes (rich blocks are now present; ephemeral sends leave `chat.messages`); verify the fragment renders in the docs build
- [ ] 6.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, and the docs build; verify all pass
- [ ] 6.3 Validate the change with `openspec validate model-rich-content-and-ephemeral-sends --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive model-rich-content-and-ephemeral-sends`) once the implementation PR into `feature/testing` is merged, which folds the delta into `openspec/specs/bot-testing-environment/spec.md`.
