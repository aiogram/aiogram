## Why

Testing an aiogram bot today means either calling handlers directly with `AsyncMock`
objects — which skips filters, middlewares and DI entirely — or hand-assembling raw
update dictionaries and a `MockedBot`-style session per project, as
`docs/dispatcher/testing.rst` currently recommends. Every non-trivial bot reinvents the
same scaffolding: fabricating `Message`/`Chat`/`User` payloads with plausible ids and
timestamps, wiring a session that does not hit the network, and asserting on outgoing
API calls one deque `pop()` at a time. Nothing models the *conversation*: there is no
way to say "this user in this group sends /start" and then assert on what the chat now
contains, so multi-step flows (FSM scenes, callback queries, edits, pinned messages)
are effectively untested in the wild.

aiogram already owns everything needed to close this gap — the generated method/type
metadata describes every request and its `__returning__` type, `Dispatcher.feed_update`
is the real entry point of the routing pipeline, and `BaseSession` is a documented
extension point. The missing piece is a supported, batteries-included integration
testing layer.

## What Changes

- New hand-written package `aiogram/test/` providing a **stateful fake Telegram
  server**: chats, users, chat members, and messages are real objects that Bot API calls
  mutate. `sendMessage` appends a `Message` to a chat, `editMessageText` mutates it,
  `deleteMessage` removes it, `banChatMember` changes a member's status.
- An **environment blueprint** describing the world (chats, users, memberships, bot
  identity, defaults). Blueprints are declarative and immutable; each test materializes
  its own isolated environment instance from one, so configuration is shareable at any
  pytest scope while no mutable state is ever shared between tests.
- **Actor-driven event triggering**: `await user.send("/start")`, `user.in_(chat)`,
  `await user.click(button)`, `await user.edit(message, ...)` build a schema-valid
  `Update` and feed it through the real `Dispatcher`, returning the handler result.
- **Every Bot API method is intercepted.** Calls the environment models are applied to
  its state; all others are recorded and answered with a schema-valid result
  auto-synthesized from the method's `__returning__` type. Per-test overrides
  (`env.on(SendMessage).returns(...)` / `.raises(TelegramBadRequest(...))`) take
  precedence, so no test needs to pre-register results just to keep the bot running.
- A **call log** with typed querying (`env.calls.last(SendMessage)`, `.count()`,
  `.filter()`) for assertions about requests, alongside state assertions on the fake
  world.
- A **pytest plugin** registered via a `pytest11` entry point, so fixtures are available
  without conftest boilerplate; `pytest` itself stays an optional extra
  (`aiogram[test]`) and is never imported by `aiogram/test/` at framework import time.
- Documentation: `docs/dispatcher/testing.rst` rewritten around the toolkit, with the
  existing direct-call and `feed_raw_update` recipes kept as the low-level fallback.

No existing public API changes; nothing is removed. This is additive.

## Capabilities

### New Capabilities

- `bot-testing-environment`: the fake Telegram world — blueprints, environment
  instances, chats/users/members/messages state, actor-driven event triggering,
  Bot API interception with state mutation, response synthesis, overrides, and the
  recorded call log.
- `bot-testing-pytest`: the pytest integration — plugin registration, the fixture set
  and its scopes, per-test isolation guarantees, blueprint sharing across tests, and
  failure reporting.

### Modified Capabilities

None. The toolkit is built on existing extension points (`BaseSession`,
`Dispatcher.feed_update`, `Bot(session=...)`) without changing their contracts.

## Impact

- **New code**: `aiogram/test/**` — hand-written, outside the `butcher` codegen
  boundary, but it *reads* generated metadata (`TelegramMethod.__returning__`, pydantic
  model fields) rather than duplicating it, so new Bot API versions are absorbed
  automatically.
- **Packaging**: new optional extra `test` in `pyproject.toml` and a
  `[project.entry-points.pytest11]` entry. No new runtime dependency for users who do
  not install the extra.
- **Docs**: `docs/dispatcher/testing.rst` rewritten; new API reference pages under
  `docs/api/` are hand-written (this package is not covered by the codegen doc
  templates).
- **Tests**: new suite under `tests/test_testing/`, held to the repo's 100% coverage
  expectation. The toolkit must also be exercised against the framework's own features
  (FSM, scenes, filters, middlewares) to prove the pipeline is real, not simulated.
- **Compatibility surface**: Python 3.10–3.14 and PyPy 3.11, all three CI operating
  systems. Response synthesis must not depend on Redis/Mongo or any optional extra.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Risk**: the fake server's fidelity is the main hazard — a state model that diverges
  from real Telegram behavior produces green tests for broken bots. Scope is bounded
  explicitly in the specs, and unmodeled methods degrade to record-and-synthesize rather
  than pretending to have semantics.
