# Tasks

## 1. Ephemeral stores and outgoing sends

- [x] 1.1 Add the outgoing and incoming ephemeral stores to `ChatState` with one shared per-chat id counter, binding as `add_message` does, read via `chat.ephemeral_messages(user)` and `chat.ephemeral_commands(user)` accepting a spec, state or id (design D1); verify with world-level tests for ordering, id allocation, direction separation and isolation from `chat.messages`
- [x] 1.2 Route any send carrying `ephemeral_message_parameters` through the ephemeral path in `build_message` (design D3, steps 1, 2 and 5): group/supergroup only, receiver resolved through the world, `message_id=0`, `ephemeral_message_id`, `receiver_user`, `message_thread_id`, `reply_to_message` only for a reply to a shared message; verify with tests for the returned shape, absence from `chat.messages`, a `wait_for_message` not satisfied by it, a topic send keeping its thread, `TelegramBadRequest` with nothing stored for a private chat and a channel, and `WorldLookupError` for an undeclared receiver
- [x] 1.3 Verify a non-text send (`sendPhoto` with `ephemeral_message_parameters`) and `sendRichMessage` take the same path, with one test each
- [x] 1.4 Add an "Ephemeral messages" section to `docs/dispatcher/testing.rst`: the shape, both stores and reading them back, the group-only rule with its source, and that membership is not checked; verify the docs build shows no new warnings for `testing.rst`

## 2. Ephemeral clicks, edits and deletions

- [x] 2.1 Extend the actor's button search to the outgoing messages addressed to it, ahead of the shared history, check an explicit `message=` for visibility, and extend the misdirected-click hint to name the receiver of another user's ephemeral message (design D5); verify the receiver's click dispatches a `callback_query` whose `message` carries `ephemeral_message_id` and `receiver_user`, and that another member's click by data or by `message=` fails naming the receiver
- [x] 2.2 Record the origin message with each callback query and refuse `replace_callback_query_message=True` for a callback query from an ephemeral message without consuming the pending query (design D3, step 4, and D5); verify the refusal, that a non-ephemeral origin accepts it, and that `answerCallbackQuery` is still owed
- [x] 2.3 Model `editEphemeralMessageText` (including `rich_message` through the conversion from `model-rich-message-content`), `...Caption`, `...Media`, `...ReplyMarkup` and `deleteEphemeralMessage` against the outgoing store, returning `True` and rejecting a missing target with Telegram's regular wording (design D4); verify with a test per method, a wrong-receiver edit failing, a deleted message no longer editable, the `message.edit_ephemeral_text()` and `message.delete_ephemeral()` shortcuts succeeding, and `message.edit_text()` and `message.delete()` on an ephemeral message failing
- [x] 2.4 Move those five methods from `RECORD_ONLY` to the registry, rewrite the list's comment to cover only the drafts, and update the record-only table in `docs/dispatcher/testing.rst`; verify `tests/test_testing/test_record_only.py` passes

## 3. Ephemeral commands from actors

- [x] 3.1 Make `_register_carried_message` route a carried message with an `ephemeral_message_id` to the incoming store and skip the shared-history id check for it (design D2); verify that two ephemeral commands in a row both dispatch, and that a hand-fed update and a `fields=` override land in the incoming store
- [x] 3.2 Add `ephemeral: bool = False` to `UserActor.send`, producing `message_id=0` and an `ephemeral_message_id`, carrying a bound topic's thread, and refused with `WorldLookupError` outside a group/supergroup or with a business binding; refuse actor `edit` and `reply` on an ephemeral target with a setup error, and update the `send` docstring (design D6); verify with tests for the dispatched shape, absence from `chat.messages`, `chat.ephemeral_commands(user)`, and every refusal
- [x] 3.3 Validate replies (design D3, step 3, and the regular-path refusal): an `ephemeral_message_id` reply must be ephemeral and must name an incoming message in the chat; verify that `message.reply(...)` to an ephemeral command produces an ephemeral reply to its sender with no `reply_to_message`, and that a non-ephemeral reply, a reply to an unknown id and a reply to the bot's own ephemeral message each fail with `TelegramBadRequest` and store nothing
- [x] 3.4 Document ephemeral commands in `docs/dispatcher/testing.rst` with a `send(..., ephemeral=True)` / `message.reply()` example, and note that `message.answer()` sends an ordinary shared message; verify the example matches a passing test

## 4. Changelog and integration

- [x] 4.1 Fold the user-visible changes into `CHANGES/1887.feature.rst`, including the observable change that ephemeral sends leave `chat.messages`; verify the fragment renders in the docs build
- [x] 4.2 Run `make lint`, `uv run pytest tests --cov=aiogram` with `aiogram/test` at 100% coverage, the docs build, and `graphify update .`; verify all pass
- [x] 4.3 Validate the change with `openspec validate model-ephemeral-messages --strict`; verify it reports the change as valid

## Workflow follow-up

- Archive the change (`openspec archive model-ephemeral-messages`) once its implementation PR into `feature/testing` is merged.
