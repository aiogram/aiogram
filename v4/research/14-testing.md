# 14 — Testing toolkit ("Testing World", PR #1887) in 4.0

PR #1887 adds `aiogram.test`, an integration-testing toolkit for bots, both for the framework's own suite and for
end users. Branch `origin/feature/testing` (Wave 2, #1951, 2026-10-31) is unmerged and behind dev-3.x.

**Size:**
- 17 006 lines of source in `aiogram/test/**` (20 files) and 26 235 lines of tests (about 1 880 tests).
- A 3 531-line docs page and 22k lines of OpenSpec files.
- The rest of the diff is dev-3.x work that got squashed in.
- In core it touches only `pyproject.toml`: a `pytest11` entry point, the `test` extra and `-p no:aiogram`.

## 1. What it is

| Piece | Module (lines) |
|---|---|
| Environment and the `feed()` entry, which calls the real `dp.feed_update` | `environment.py` (2 450) |
| Declarative world (`UserSpec`, `ChatSpec`, `MemberSpec`, `TopicSpec`, …) | `blueprint.py` (890) |
| In-memory Telegram state (users, chats, messages, members, topics, polls, stars, gifts, sticker sets, clock) | `world.py` (2 268) |
| Users acting: about 45 triggers (`send`, `reply`, `click`, `join`, `pay`, `react`, …) | `actors.py` (2 994) |
| Fake server behaviour for about 130 of ≈185 methods (`@models` registry, `BOT_RIGHTS`, `MEDIA_FIELDS`) | `modeling.py` (4 194) |
| Server-side HTML / MarkdownV2 / Markdown parser | `markup.py` (1 277) |
| Schema-valid result synthesis for methods with no fake behaviour | `synthesis.py` (320) |
| 85 hand-written rejections → production exceptions; per-chat 429 | `rejections.py` (474), `errors.py`, `flood.py` |
| Overrides: `env.on(Method, …).returns/raises`, `env.blocked(...)` | `overrides.py` (716) |
| pytest plugin: fixtures, `assert_updates_handled`, assertion repr | `plugin.py` (269) |
| Call interception: `FakeTelegramSession(BaseSession)` | `session.py` (71) |

## 2. Decisions (D51–D54)

| # | Decision |
|---|---|
| **D51** | **Part of the core distribution, with an opt-in plugin.** `aiogram.test` ships inside the single `aiogram` wheel (D17), because its generated parts must match the installed API. There is **no `pytest11` entry point**: users enable it with `-p aiogram.test.plugin` or `pytest_plugins = ["aiogram.test.plugin"]`. The `aiogram[test]` extra pulls in pytest. aiogram's own suite then needs no `-p no:aiogram` workaround |
| **D52** | **Calls are intercepted at the typed level (as today)**: the fake receives method objects and never runs the Rust encoder/decoder. Codec fidelity is covered by the codec's own tests and the request differential harness (08 §5, 13 B8) |
| **D53** | **Identity through cache seeding** (01 §3.1). A Rust constructor puts the objects passed to it into the child wrapper cache, so `Update(message=m).message is m` holds for unbound construction. Scope revised by D103: identity holds **within one view**, not across `as_()`. The world therefore builds updates **already bound** to the target bot, so the dispatcher never remounts them, and the toolkit keeps its promise that `message is chat.messages[-1]` inside handlers. Mechanism conditional on the spike gate (D104) |
| **D54** | **An official dispatcher trace hook** (span context managers, D63; the toolkit uses the callback adapter) (03 §5, "Instrumentation") replaces the toolkit's middleware injection for route diagnostics. The OpenTelemetry PR #1787 and logging use the same hook. For per-test setup, use a fresh `Dispatcher` per environment, or mutate it and call `runner.refresh()` (or restart), since each Runner routes on a snapshot (D114). There is no swapping of `dp.fsm.storage` / `workflow_data` while running |

## 3. Port to 4.0 (defaults)

- **Delivery:** a `WorldSource` implements `UpdateSource` (12 §4) and calls `runner.feed(bot, update)`. Tests then get the
  real lifecycle (`startup`/`shutdown`, `bot_added`), Runner task tracking (which replaces most of the task-factory
  wrapping) and `runtime_errors` (D50) for background failures. Direct `env.feed()` stays as a convenience.
- **Generated from the IR (02):**
  - result synthesis (from IR-generated tables; no runtime introspection, D95);
  - `Default`-field resolution (replaces the copy of `prepare_value`);
  - the `MEDIA_FIELDS` / `BOT_RIGHTS` tables and the posted-content table (replaces `ContentType`, which is removed);
  - per-update-type trigger coverage.

  Butcher `check` fails when a new method has neither a fake model nor an explicit `synthesize` mark, so fake
  coverage keeps up with each Bot API release.
- **Hand-written:** world mutation, actors, the markup parser, rejection texts. Rejection texts may move into an
  overlay file beside `errors.json`, using `ErrorReason` (D47).
- **Rewritten:**
  - `mounting.py`, because binding is now an independent bound view (D103, 01 §3.2) and the world builds updates already bound;
  - `__pydantic_extra__` → `obj.raw` (D91, D108);
  - route diagnostics on D54 and D49 (`ErrorEvent.handler/router/phase`).
- **Overrides:** `dp.dependency_overrides` (D32) is the native way to swap dependencies. `env.on(...)` stays for
  Bot API responses.
- **Flood:** `flood.py` 429s exercise `RetryMiddleware` / `RateLimitMiddleware` (D43/D44). Their sleeps run on the
  world clock or under looptime.
- **Forward compatibility:** the world can emit `Unknown…` union members and unknown update types (D10) for fuzzing.
- **Fidelity:** recorded real-API traces (redacted, with provenance) and hand-curated wire fixtures are replayed
  through the differential harness (08 §5) against the fake's responses for the modelled methods. The fake marks
  **modelled versus synthesised** methods visibly, so a synthetic result is never mistaken for server behaviour (R26).
- **Difference manifests (R26):** each differential case is classed invariant, approved difference (with a
  decision id and a narrow assertion) or newly supported; 4.0's intended changes are approved differences, not
  snapshot exclusions.
- **Free-threading:** documented as **single-loop only**; the `World` has no locks.
- **Branch:** rebase onto dev-3.x first, then port during roadmap phase 4.
- **Dogfooding (D88):** `MockedBot` stays for unit tests of single components. New end-to-end integration tests
  (dispatcher + FSM + scenes + filters + errors) use the toolkit. There is no mass rewrite.
- **OpenSpec (D89):** all OpenSpec files (`openspec/**`, about 22k lines) are **dropped** from the merge and stay in
  branch history only. `docs/dispatcher/testing.rst` (moving into the D80 structure) is the specification.
