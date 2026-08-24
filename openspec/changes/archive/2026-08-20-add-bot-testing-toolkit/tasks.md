## 1. Package skeleton and packaging

- [x] 1.1 Create `aiogram/test/` with `__init__.py`, `blueprint.py`, `world.py`, `session.py`, `synthesis.py`, `calls.py`, `actors.py`, `environment.py`, `errors.py`, `plugin.py`; `__init__.py` must not import pytest
- [x] 1.2 Add the `test = ["pytest>=8,<10"]` optional extra and `[project.entry-points.pytest11] aiogram = "aiogram.test.plugin"` to `pyproject.toml`
- [x] 1.3 Add a test asserting `import aiogram.test` succeeds with pytest absent from the import graph (assert `plugin` is not imported by `__init__`)
- [x] 1.4 Create `tests/test_testing/` with `__init__.py` mirroring the package layout

## 2. World model

- [x] 2.1 Implement `ChatState`, `UserState`, `MemberState`, `MessageRecord` mutable dataclasses in `world.py`, plus per-chat `message_id` and global `update_id` counters
- [x] 2.2 Implement conversion from world objects to `aiogram.types` (`Chat`, `User`, `ChatMember*`, `Message`) at the boundary
- [x] 2.3 Implement the world registry: lookup of chats/users/members by id, membership status transitions, message insert/edit/delete/pin
- [x] 2.4 Tests: world state transitions, id allocation, conversion round-trips

## 3. Blueprint

- [x] 3.1 Implement frozen `Blueprint` with declarations for chats, users, memberships, bot identity and `DefaultBotProperties`
- [x] 3.2 Implement `Blueprint.build()` materializing a fresh world with deep-copied state
- [x] 3.3 Provide a default blueprint (one private chat, one user, one bot identity) used when a test declares nothing
- [x] 3.4 Tests: two environments from one blueprint do not observe each other's mutations; blueprint itself is unmodified after builds

## 4. Response synthesis

- [x] 4.1 Implement the cached per-type factory builder in `synthesis.py` driven by pydantic field metadata (no `typing` internals — see design D4/PyPy risk)
- [x] 4.2 Handle scalars, `datetime`, nested models, discriminated unions (resolve by tag), plain unions, lists, and optional-field omission
- [x] 4.3 Seed world-known fields (`chat`, `from_user`, `message_id`) from the environment when unambiguous
- [x] 4.4 Raise a clear error naming the type, the field and the override to write when a required field cannot be filled
- [x] 4.5 Test parametrized over **every** generated method's `__returning__` type, asserting synthesis produces a valid instance — this is the guard that catches future Bot API shapes

## 5. Session interception and `Default` resolution

- [x] 5.1 Implement `TestSession(BaseSession)` with `make_request` routing into the override → model → synthesize ladder
- [x] 5.2 Implement typed `Default` resolution (`model_copy(update=…)` against `bot.default`) applied before recording and before state mutation
- [x] 5.3 Guard test: for every method with a `Default`-bearing field, typed resolution agrees with `BaseSession.prepare_value` (mirrors `TestParseModeDefaultIsWired`)
- [x] 5.4 Implement `stream_content` as an inert generator so download paths do not hit the network
- [x] 5.5 Tests: no network access, no valid token required, session closes cleanly

## 6. Modeled Bot API methods

- [x] 6.1 Implement the method-handler registry and its dispatch from `TestSession`
- [x] 6.2 Model message creation: `SendMessage`, `SendPhoto`, `SendDocument` and the remaining `Send*` media methods
- [x] 6.3 Model message mutation: `EditMessageText`, `EditMessageCaption`, `EditMessageReplyMarkup`, `DeleteMessage`, `DeleteMessages`
- [x] 6.4 Model message movement: `ForwardMessage(s)`, `CopyMessage(s)`, `PinChatMessage`, `UnpinChatMessage`
- [x] 6.5 Model membership and chat queries: `BanChatMember`, `UnbanChatMember`, `PromoteChatMember`, `RestrictChatMember`, `GetChatMember`, `GetChat`, `LeaveChat`
- [x] 6.6 Model `AnswerCallbackQuery` (record + acknowledge) and `GetMe` (blueprint identity)
- [x] 6.7 Tests per modeled group: state after the call, returned object consistency, and the unmodeled fallback still recording

## 7. Errors

- [x] 7.1 Implement failure construction routed through `BaseSession.check_response` so framework exception types and descriptions match production
- [x] 7.2 Model the invalid-operation errors named in the spec (editing/deleting a missing message, acting on an unknown chat)
- [x] 7.3 Tests: exception types propagate to handlers, and the dispatcher error pipeline receives them

## 8. Call log

- [x] 8.1 Implement the ordered recorder storing resolved `TelegramMethod` objects
- [x] 8.2 Implement typed queries: `last(Method)`, `all(Method)`, `count(Method)`, `filter(predicate)`
- [x] 8.3 Tests: ordering, typed lookup, empty-log assertions

## 9. Overrides

- [x] 9.1 Implement `env.on(Method).returns(...)` / `.raises(...)` with optional call-count limits
- [x] 9.2 Enforce precedence over modeling and synthesis, and per-environment scoping
- [x] 9.3 Tests: consecutive calls with different outcomes; overrides do not leak between environments

## 10. Environment and actors

- [x] 10.1 Implement `BotTestEnvironment` owning the `Bot`, the supplied `Dispatcher`, the world, the recorder and the overrides
- [x] 10.2 Implement storage swapping and `workflow_data` capture/restore on dispose, restored in a `finally` (design D7)
- [x] 10.3 Implement `detach_router()` for re-including module-level router trees
- [x] 10.4 Implement actors: `user.in_(chat)` binding plus `send`, `edit`, `click`, `join`, `leave`, `inline_query` triggers building schema-valid updates and awaiting `feed_update`
- [x] 10.5 Resolve `click` targets from a stored message's real `reply_markup`
- [x] 10.6 Expose FSM context read/write for a `(user, chat)` pair
- [x] 10.7 Tests: handler return value propagation, DI kwargs passthrough, `event_from_user`/`event_chat` resolution, filters and middlewares not bypassed

## 11. pytest plugin

- [x] 11.1 Implement `plugin.py` with fixtures: `bot_blueprint`, `bot_dispatcher`, `bot_env`, `bot`, and default chat/user accessors
- [x] 11.2 Make `bot_env` function-scoped with guaranteed disposal on pass and on failure; keep `bot_blueprint` overridable at any scope
- [x] 11.3 Add assertion representation hooks (`pytest_assertrepr_compare`) for world and call-log types
- [x] 11.4 Ensure no event-loop policy or asyncio plugin is imposed
- [x] 11.5 Tests via `pytester`: fixtures resolve with no conftest; isolation holds with a session-scoped blueprint; environment disposed after a failing test

## 12. Framework-level integration proof

- [x] 12.1 End-to-end test driving an FSM flow (states, data, transitions) through the toolkit
- [x] 12.2 End-to-end test driving a Scene flow, including a `chat_member`/`channel_post`-adjacent path
- [x] 12.3 End-to-end test covering a middleware that injects data and a filter that rejects
- [x] 12.4 End-to-end test of a callback-query flow: bot sends a keyboard, user clicks, handler edits the message, test asserts final chat state

## 13. Documentation

- [x] 13.1 Rewrite `docs/dispatcher/testing.rst` around the toolkit, keeping direct-call and `feed_raw_update` as the documented low-level fallback
- [x] 13.2 API reference — placed inside `docs/dispatcher/testing.rst` (already in the toctree) rather than under `docs/api/`, which is the *generated* Bot API section
- [x] 13.3 Document the required async pytest configuration and the router-attachment constraint
- [x] 13.4 Build docs (`rtk proxy uv run --extra docs bash -c 'cd docs && make html'`) and fix warnings

## 14. Release readiness

- [x] 14.1 `CHANGES/<issue-or-pr>.feature.rst` describing the toolkit in user-visible terms
- [x] 14.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 14.3 Verify the new suite passes without the `redis`/`mongo` options and on the 3.10 floor (no 3.11+ syntax; mypy targets 3.10)
- [x] 14.4 Review with the `aiogram-pr-gate` agent before opening the PR
