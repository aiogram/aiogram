## Context

aiogram already exposes the three seams this toolkit needs:

- `BaseSession.make_request(bot, method, timeout)` — the single choke point every Bot API
  call passes through. `tests/mocked_bot.py` already uses it, but as a bare deque of
  canned responses with no world model.
- `Dispatcher.feed_update(bot, update, **kwargs)` — the real entry point of the routing
  pipeline; polling and webhook both funnel into it.
- Generated metadata — every `TelegramMethod` subclass declares `__returning__`, and
  every type is a pydantic model with introspectable fields. This is what makes generic
  response synthesis possible without a hand-maintained table.

Two facts from the codebase shape the design more than anything else:

1. **`Default(...)` sentinels are resolved late.** `BaseSession.prepare_value`
   (`aiogram/client/session/base.py:179`) substitutes them during serialization. A
   session that intercepts `make_request` therefore receives the method object with
   sentinels *still in place*, and must resolve them itself before recording or applying
   state.
2. **A `Router` can be attached to exactly one parent, ever.**
   `Router.parent_router` raises `RuntimeError("Router is already attached to …")`
   (`aiogram/dispatcher/router.py:232`). Since real bots declare routers at module import
   time, a naive "fresh `Dispatcher` per test" design fails on the second test in a run.

## Goals / Non-Goals

**Goals:**

- Integration testing of the full pipeline: filters, middlewares, DI, FSM, routers.
- A world model faithful enough that assertions about *what the chat now looks like* are
  meaningful, not just what calls were made.
- Zero per-test setup for the common case; every Bot API call works out of the box.
- Absorb new Bot API versions automatically — no per-method table to maintain.
- Test isolation that is structural, not disciplinary.

**Non-Goals:**

- Simulating Telegram's business rules in full (rate limits, permission matrices,
  media processing, message-age limits on edit/delete). The fake models *shape*, not
  policy.
- Testing the webhook HTTP layer or polling loop. Both reduce to `feed_update`, which is
  what the toolkit drives; `aiohttp` server testing stays out of scope.
- Multi-bot environments and cross-bot interaction.
- Real network, real tokens, VCR-style record/replay against live Telegram.
- Load or concurrency testing.

## Decisions

### D1. Interception at the session layer, not by patching `Bot`

A `TestSession(BaseSession)` implements `make_request` and dispatches to the world model.
This keeps `Bot` untouched, inherits `check_response` error semantics, and means handler
code, shortcuts and `bot.__call__` all work unmodified.

*Alternative rejected:* monkeypatching `Bot.__call__` — invisible to code holding a bound
method, and would bypass the framework's own error conversion.

### D2. Resolve `Default` sentinels before the world sees a call

`TestSession` performs a typed resolution pass over the method object: any field whose
value is a `Default` instance is replaced with `bot.default[name]`, producing a new method
instance via `model_copy(update=…)`. Both the call log and the state model consume the
resolved object.

This is deliberately *not* `prepare_value`, which flattens everything to JSON-ready
primitives and would destroy the typed objects tests assert on. The cost is a second,
smaller resolution implementation that must stay in step with `prepare_value` — covered
by a test that asserts both agree for every method carrying a `Default`, in the spirit of
the existing `TestParseModeDefaultIsWired` guard.

### D3. Three-tier call handling: override → model → synthesize

Every intercepted call goes through the same ladder:

1. **Override** — a test-declared outcome for this method type (result or exception),
   optionally limited to N calls.
2. **Model** — a registered handler for methods with world semantics
   (`SendMessage`, `EditMessageText`, `DeleteMessage`, `ForwardMessage`, `CopyMessage`,
   `PinChatMessage`, `AnswerCallbackQuery`, `BanChatMember`, …). Applies the mutation and
   returns a state-consistent result.
3. **Synthesize** — anything else: build a schema-valid instance of `__returning__`.

Tier 3 is what makes the toolkit survive Bot API bumps: a new generated method is
answered correctly without touching this package. Tier 2 is an explicit, bounded list —
the spec names it, so its growth is a deliberate decision rather than drift.

*Alternative rejected:* requiring registration for everything (today's `MockedBot`
behavior). It scales badly: a bot that calls `getChatMember` inside a filter would need
that registered in every test that touches any handler.

### D4. Response synthesis by cached model introspection

For a target type, walk pydantic model fields: required fields get a value by kind —
`int` from a monotonic counter, `str` from the field name, `bool` `True`, `datetime` a
fixed base time plus offset, nested models recursively, discriminated unions resolved to
the member matching the tag, plain unions to their first member, `list[...]` to `[]`
unless required-non-empty. Optional fields are left unset. Per-type factories are built
once and cached (`functools.lru_cache`), so synthesis is a dict build at call time.

Known-entity fields are seeded from the world where the name makes it unambiguous
(`chat`, `from_user`, `message_id`), which is what makes synthesized results read like
they belong to the environment rather than being noise.

*Risk accepted:* synthesis can produce a semantically odd but schema-valid object. That is
the point — tests that care assert with an override; tests that do not, do not break.

### D5. The world model is plain mutable objects, distinct from Bot API types

The environment stores `ChatState`, `UserState`, `MemberState`, `MessageRecord` — small
mutable dataclasses — and converts to `aiogram.types` objects at the boundary. Storing
frozen pydantic API types directly would force a rebuild on every edit and make identity
tracking (`message_id` → record) awkward.

`message_id` is allocated per chat from a counter, matching Telegram's per-chat numbering;
`update_id` is global and monotonic.

### D6. Blueprint is frozen; environments are materialized copies

`Blueprint` and its members are frozen dataclasses with no runtime state. `Blueprint.build()`
returns a fresh `BotTestEnvironment` with deep-copied world state. Isolation then needs no
teardown discipline: sharing a blueprint at session scope is safe because there is nothing
mutable to share. This directly satisfies the isolation requirements in
`bot-testing-pytest` without snapshot/rollback machinery.

### D7. Dispatcher lifetime: reuse the project's, swap the storage

Because of the router-attachment constraint (`Router` → one parent forever), the toolkit
must not assume a fresh `Dispatcher` per test. Instead:

- The `dispatcher` fixture may be any scope, including session.
- On environment build, the environment swaps `dispatcher.fsm.storage` for a fresh
  `MemoryStorage` and restores the original on dispose. This guarantees FSM isolation even
  when the project's real dispatcher uses `RedisStorage`.
- `Dispatcher.workflow_data` mutations made during a test are captured and restored the
  same way.
- For projects that *do* build routers per test, a `detach_router()` helper clears
  `_parent_router` recursively so a module-level router tree can be re-included.

*Alternative rejected:* forcing a function-scoped dispatcher. It breaks the dominant
real-world pattern (module-level `router = Router()`) and would make the toolkit's first
impression a `RuntimeError`.

### D8. Actors are bindings, not state

`user.in_(chat)` returns a lightweight actor bound to a `(user, chat)` pair; triggers are
methods on it (`send`, `edit`, `click`, `join`, `leave`, `inline_query`). Each builds an
`Update` and awaits `dispatcher.feed_update(bot, update, **kwargs)`, returning the handler
result so the existing `feed_raw_update` assertion style still works.

Callback triggers resolve the button from a stored message's real `reply_markup`, so a
test clicks *the button the bot actually sent* rather than a hand-copied `callback_data`
string — the single highest-value affordance of the whole toolkit.

### D9. Packaging: `aiogram.test` + optional extra + `pytest11` entry point

`aiogram/test/` is hand-written and lives outside the `butcher` boundary. `pyproject.toml`
gains `test = ["pytest>=8,<10"]` and
`[project.entry-points.pytest11] aiogram = "aiogram.test.plugin"`. `aiogram/test/__init__.py`
must not import pytest; only `plugin.py` does, and pytest imports it via the entry point.
Everything reachable through fixtures is also importable directly.

*Alternative considered:* module name `aiogram.testing`, marginally more readable and no
association with CPython's `test` package. `aiogram.test` was chosen for brevity and to
match the option selected during proposal; it is cheap to rename before release, and
impossible after.

### D10. Errors are the framework's own exceptions

Modeled failures raise `aiogram.exceptions.TelegramBadRequest` / `TelegramForbiddenError`
etc. with a description matching Telegram's wording where known. The toolkit reuses
`BaseSession.check_response` rather than raising directly, so the error path under test is
the production error path.

## Risks / Trade-offs

- **Fidelity gap → false green.** A world model that diverges from Telegram passes tests
  for broken bots. → Bound the modeled set explicitly in the spec, degrade unmodeled
  methods to record-and-synthesize instead of guessing semantics, and document that the
  toolkit tests *the bot's logic*, not Telegram's rules.
- **`Default` resolution drift (D2).** A second resolver can fall out of step with
  `prepare_value`. → A guard test asserting both agree across every method with a
  `Default`-bearing field; failure is a build break, not a silent divergence.
- **Synthesis breaks on an unusual generated shape.** A future Bot API type with a
  required field the walker cannot fill. → Fail loudly with a message naming the type and
  field plus the override to write; add a suite that synthesizes *every* generated return
  type so a bad shape is caught in aiogram's own CI, not in a user's.
- **Storage swapping touches a user object (D7).** Restoring on dispose is a correctness
  requirement; a crashed test must not leave the project's dispatcher pointed at a dead
  `MemoryStorage`. → Restore in a `finally`, and cover the crash path in tests.
- **Public API surface growth.** Everything exported becomes a support obligation across
  the framework's compatibility window. → Keep the exported surface small and named in the
  spec; anything not in the spec stays private.
- **Coverage cost.** The repo expects 100%; this package is large and mostly branchy
  construction code. → Budget test work at roughly the size of the implementation, and
  favor data-driven tests over the generated metadata (parametrizing over every method
  type) rather than hand-written per-method cases.
- **PyPy and Python 3.10–3.14.** Synthesis leans on typing introspection, historically the
  most version-sensitive area in this repo (#1741 was exactly this). → No
  `typing`-internals access; go through pydantic's own field metadata, which the framework
  already relies on across the whole matrix.

## Migration Plan

Purely additive; no migration. Rollout:

1. Land the package with the extra unadvertised, exercised by aiogram's own tests.
2. Rewrite `docs/dispatcher/testing.rst` around the toolkit, keeping the current
   direct-call and `feed_raw_update` recipes as the documented low-level fallback.
3. Announce in the changelog as a feature.

Rollback is removal of the package and the extra; nothing in the framework depends on it.

## Open Questions

- Should `aiogram.test` re-export a `pytest.mark`-style marker for declaring the blueprint
  inline (`@pytest.mark.bot_env(...)`) in addition to fixture overrides? Deferred until the
  fixture ergonomics are proven in the repo's own suite.
- How far should chat-member permission modeling go — status transitions only, or the full
  `ChatPermissions` matrix? Starting with status transitions; the matrix is a candidate
  follow-up once real usage shows demand.
- Whether media/file handling should synthesize a `File` with a fake `file_path` that
  `bot.download` can serve from an in-memory store, or stay record-only in v1. Leaning
  record-only.
