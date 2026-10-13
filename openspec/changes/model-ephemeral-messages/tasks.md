# Tasks

## 1. Outgoing ephemeral messages

- [ ] 1.1 Add the per-chat ephemeral store to `ChatState` (keyed by receiver and ephemeral id, own id counter, binding as `add_message` does) with `chat.ephemeral_messages(user)` accepting a spec, state or id (design D1); verify with world-level tests for ordering, id allocation and isolation from `chat.messages`
- [ ] 1.2 Route any send carrying `ephemeral_message_parameters` through an ephemeral path in `build_message` (design D2): group/supergroup only, receiver must be a member, `message_id=0`, `ephemeral_message_id`, `receiver_user`; verify with tests for the returned shape, absence from `chat.messages`, a `wait_for_message` that is not satisfied by it, and `TelegramBadRequest` with nothing stored for a non-member receiver and for a private chat and a channel
- [ ] 1.3 Verify a non-text send (`sendPhoto` with `ephemeral_message_parameters`) and `sendRichMessage` take the same path, with one test each
- [ ] 1.4 Add an "Ephemeral messages" section to `docs/dispatcher/testing.rst` covering the shape, the store and reading it back; verify the docs build shows no new warnings for `testing.rst`

## 2. Ephemeral clicks, edits and deletions

- [ ] 2.1 Extend the actor's button search to the ephemeral messages addressed to it, and the misdirected-click hint to name the receiver of another user's ephemeral message (design D5); verify that the receiver's click dispatches a `callback_query` whose `message` carries `ephemeral_message_id` and `receiver_user`, and that another member's click fails naming the receiver
- [ ] 2.2 Model `editEphemeralMessageText` (including `rich_message` through the conversion from `model-rich-message-content`), `...Caption`, `...Media`, `...ReplyMarkup` and `deleteEphemeralMessage` against the store, returning `True` and rejecting a missing target with Telegram's regular wording (design D4); verify with a test per method, a test that a deleted message can no longer be edited, and a test that drives `message.edit_ephemeral_text()` and `message.delete_ephemeral()` shortcuts
- [ ] 2.3 Move those five methods from `RECORD_ONLY` to the registry and update the record-only table in `docs/dispatcher/testing.rst` (drafts stay); verify `tests/test_testing/test_record_only.py` passes

## 3. Ephemeral commands from actors

- [ ] 3.1 Add `ephemeral: bool = False` to `UserActor.send` producing `message_id=0` and an `ephemeral_message_id`, stored in the ephemeral store under the sender with no `receiver_user`, and refused with `WorldLookupError` outside a group/supergroup or with a business binding (design D1, D6); verify with tests for the dispatched shape, absence from `chat.messages` and both refusals
- [ ] 3.2 Validate `reply_parameters.ephemeral_message_id` on sends (design D3): the request must be ephemeral and the id must name an incoming ephemeral message in the chat; verify with tests that `message.reply(...)` to an ephemeral command produces an ephemeral reply to its sender, and that a non-ephemeral reply and a reply to an unknown id fail with `TelegramBadRequest` and store nothing
- [ ] 3.3 Document ephemeral commands in `docs/dispatcher/testing.rst` with a `send(..., ephemeral=True)` / `message.reply()` example; verify the example matches a passing test

## 4. Changelog and integration

- [ ] 4.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the observable change that ephemeral sends leave `chat.messages`; verify the fragment renders in the docs build
- [ ] 4.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, and the docs build; verify all pass
- [ ] 4.3 Validate the change with `openspec validate model-ephemeral-messages --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive model-ephemeral-messages`) once its implementation PR into `feature/testing` is merged.
