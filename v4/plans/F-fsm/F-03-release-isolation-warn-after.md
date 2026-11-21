# F-03 — `state.release_isolation()`, `isolation_warn_after`, release hooks, re-entrancy error

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-02](F-02-isolation-lock-table-default-on.md), [A-11](../A-contracts/A-11-migration-registry.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md) |
| Blocks | [F-13](F-13-scenes-d33.md), [F-16](F-16-race-suite-314t.md), [F-17](F-17-fsm-docs-migration-page.md), [G-02](../G-features/G-02-depends-scope-teardown.md), [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md), [I-19](../I-distribution/I-19-heuristic-behaviour-rules.md), [E-11](../E-runtime/E-11-error-model-bubbling.md) |
| Gate-conditional | no |
| Decisions | D28, D110, D112, PD-04, PD-26 |
| Sources | [19 D110, D112](../../research/19-review-resolutions.md), [04-fsm.md §4 (D28)](../../research/04-fsm.md), [README breaking change 15](../../research/README.md), [codex-review.md R14](../../research/codex-review.md), [15-observability.md](../../research/15-observability.md), [plans README §1 PD-04, PD-26](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

With isolation on by default (D28, F-02), handlers that wait for a *later* update of the same FSM key deadlock: "ask
and wait" helpers and re-entrant `feed_update` (README breaking change 15). D110 adds the escape hatch
`async with state.release_isolation():` and a warning when a key's lock is held longer than `isolation_warn_after`
(default 30 s). PD-26 turns the same-task re-entrant deadlock into a `RuntimeError`. PD-04 puts Depends teardown
**inside** the isolation scope, so G-02 needs a hook that runs before the lock is released.

Today `FSMContext` (`aiogram/fsm/context.py`) knows nothing about isolation, and `FSMContextMiddleware.__call__`
(`aiogram/fsm/middleware.py`) holds the lock in a bare `async with`.

## Scope

**In:**
- `FSMContextMiddleware` passes the isolation handle into the `FSMContext` it creates (new optional constructor
  argument; manual `FSMContext(storage, key)` keeps working without one).
- `FSMContext.release_isolation()` → async context manager: releases the key's lock on enter, re-acquires it on exit
  (FIFO like any waiter). Behaviour by isolation:
  - `SimpleEventIsolation`: real release/re-acquire through the F-02 handle;
  - `DisabledEventIsolation` or no handle: no-op;
  - `RedisEventIsolation`: releases and re-acquires the redis-py lock;
  - custom `BaseEventIsolation` whose `lock()` yields `None`: raises `NotImplementedError` naming the isolation class.
- After re-acquire, `raw_state` injected at middleware time may be stale; `release_isolation` docs say to call
  `await state.get_state()` again.
- **Release hooks (PD-04):** the handle exposes `add_release_hook(hook: Callable[[], Awaitable[None]]) -> None`; hooks run LIFO
  **inside** the lock, after the handler chain (including `errors` handlers) and before the final release — at E-11's
  `close_point`, which is the only caller (exit of `FSMContextMiddleware.__call__`, or the end of `feed_update` when
  FSM is off). Temporary releases by
  `release_isolation` do not run them. A failing hook never skips the release (`try/finally`); its exception is
  passed to the caller-supplied reporter (E-11's `close_point` sends it to `dp.runtime_errors` with `phase=TEARDOWN`,
  D112). Updates without an
  FSM key (no lock) still get a scope object with the same hook API, run at the same point, so G-02 has one code path.
- **Re-entrancy (PD-26):** acquiring a key whose holder is the **current task** (`asyncio.current_task()`) raises
  `RuntimeError` with the key and a pointer to `release_isolation`. Owner identity is the task object, not a
  context variable, so child tasks waiting on the key are not affected.
- **Hold-time warning (D110):** see the decision below.

**Out:**
- Depends itself and teardown error routing: G-02.
- Lock table internals: [F-02](F-02-isolation-lock-table-default-on.md).
- Toolkit helpers that wait for replies: H-17 consumes this API.

## Checklist

- [ ] Decide where `isolation_warn_after` is configured and which channel the warning uses (**proposed default:**
      `SimpleEventIsolation(warn_after=30.0)` and `RedisEventIsolation(warn_after=30.0)`, plus
      `Dispatcher(isolation_warn_after=30.0)` forwarded to the default isolation; `None` disables. Channel: `logging`
      WARNING on the `aiogram.fsm` logger (H-01) with structured `extra` (key, held seconds), not `warnings.warn`,
      because it is an operational event that should repeat per occurrence. Measurement adds no cost to the
      uncontended path: check at release time, and on the contended path a waiter arms one `loop.call_later` that
      reports a holder still holding after `warn_after`) — record in Notes and flag to owner.
- [ ] Handle API on the F-02 handle: `release()` / `reacquire()` (private), `add_release_hook(hook: Callable[[],
      Awaitable[None]]) -> None` (public, documented for integrations); the no-key scope object exposes the same
      method.
- [ ] `FSMContext.release_isolation()`; `FSMContextMiddleware` wires the handle and runs release hooks.
- [ ] `RedisEventIsolation` handle support (release + re-acquire of the redis-py lock; `warn_after`). Document that
      the default redis-py lock `timeout=60` (`DEFAULT_REDIS_LOCK_KWARGS`) expires a lock held longer than 60 s.
- [ ] PD-26 re-entrancy check in `SimpleEventIsolation` (and in `RedisEventIsolation`, which tracks its own holder
      task per key in-process).
- [ ] Tests: ask-and-wait pattern (handler A waits for update B of the same key inside `release_isolation`) completes;
      the same without it raises `RuntimeError` for re-entrant same-task `feed_update` and, for the cross-task case,
      the hold-time warning fires (`caplog`, `warn_after=0.05`); hooks run LIFO inside the lock, after `errors`
      handlers, and a failing hook still releases; no-op on `DisabledEventIsolation`; `NotImplementedError` on a
      custom isolation.
- [ ] Docs: breaking change 15 recipe (`async with state.release_isolation():`) in the FSM docs (F-17 integrates).
- [ ] Tests (100% coverage of new code)
- [ ] Migration-registry entry (PD-13): re-entrant same-key `feed_update` now raises `RuntimeError`; ask-and-wait
      helpers need `release_isolation` (manual-checklist; I-19 heuristic rule).
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- The ask-and-wait test passes within 1 s; without `release_isolation`, the same-task re-entrant variant raises
  `RuntimeError` immediately instead of hanging.
- A lock held for `warn_after + ε` produces exactly one WARNING record on `aiogram.fsm` per hold; an uncontended update
  with the default config creates no timer (asserted by patching `loop.call_later`).
- Release hooks: order LIFO, run before the next waiter is granted (asserted by a waiter recording timestamps), and the
  lock is released even when a hook raises.
- F-02's uncontended benchmark stays within its threshold (≤ 1.0 µs).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Turn isolation off by default to avoid deadlocks | Kept on; escape hatch + warning instead | D110 |
| Teardown after the lock is released ("after the whole update") | Owner moved teardown inside the isolation scope | PD-04 (revises D112 wording) |
| Detect re-entrancy with a context variable | Child tasks inherit it and would raise although they can legitimately wait | PD-26 ("same task") |
| `warnings.warn(RuntimeWarning)` for slow holders | Deduplicated per call site; wrong tool for a recurring operational event | proposed, see checklist |

## Validation

```bash
make dev
uv run pytest tests/test_fsm tests/test_dispatcher -q
uv run pytest --redis redis://localhost:6379/0 tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Consumes the F-02 handle. G-02 consumes `add_release_hook` and the no-key scope object; the signature is fixed
  above and named identically in E-11 (call site `close_point`) and G-02 — change all three together or not at all.
- H-17 (toolkit interop) uses `release_isolation` for its wait-for-reply helpers.
- F-13 uses `release_isolation` semantics in scene docs; F-16 adds the adversarial cases.

## Notes
