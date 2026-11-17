# E-11 — Error model: `ErrorEvent` fields, phases, bubbling, update-scope hooks

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md), [E-04](E-04-router-graph-multi-parent-flags.md), [A-11](../A-contracts/A-11-migration-registry.md), [C-12](../C-butcher/C-12-enums-error-reason-emitter.md), [F-03](../F-fsm/F-03-release-isolation-warn-after.md) |
| Blocks | [E-12](E-12-runtime-errors.md), [E-14](E-14-feed-paths-forward-compat-dispatch.md), [G-02](../G-features/G-02-depends-scope-teardown.md), [H-15](../H-testing-observability/H-15-route-diagnostics-on-trace-hook.md), [E-21](E-21-e-exit-gate.md), [I-19](../I-distribution/I-19-heuristic-behaviour-rules.md) |
| Gate-conditional | no |
| Decisions | D48, D49, D112, PD-04, PD-05, README breaking change 17 |
| Sources | [03-routing.md §5 "Errors", "Dependencies"](../../research/03-routing.md), [19 D112](../../research/19-review-resolutions.md), [codex-review R17](../../research/codex-review.md), [plans README PD-04, PD-05](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

In 3.x a single `ErrorsMiddleware` (`aiogram/dispatcher/middlewares/error.py`) sits outermost on `dp.update` and, on
any exception, propagates an `ErrorEvent(update, exception)` through the **whole** tree, so sibling routers catch each
other's errors and the event says nothing about where it failed. D48: errors go to the raising router's `errors`
observer, then bubble to parents. D49: `ErrorEvent` carries `bot`, `router`, `handler`, `phase`. D112 / PD-04: Depends
providers always see the escaped exception, and teardown runs **inside the isolation scope, after `errors` handlers**.
E owns the error flow and the hook points; G-02 owns the Depends scope and teardown itself.

## Scope

**In:**
- **`ErrorEvent`** becomes a frozen dataclass (not a Bot API type) with `update`, `exception`, `bot`, `router`,
  `handler: HandlerObject | None` (None before matching), `phase: ErrorPhase`. Keep the import path
  `aiogram.types.ErrorEvent` (re-export) and `aiogram.types.error_event`; `F.exception`, `ExceptionTypeFilter`,
  `ExceptionMessageFilter` keep working.
- **`ErrorPhase(StrEnum)`** (owned here, one enum shared by `ErrorEvent` and E-12's `RuntimeErrorEvent`):
  - dispatch phases: `OUTER_MIDDLEWARE`, `FILTER`, `INNER_MIDDLEWARE`, `HANDLER`, `DECODE`, `DEPENDENCY`;
  - runtime phases: `STARTUP`, `SHUTDOWN`, `BOT_HOOK` (`bot_added` / `bot_removed`), `POLLING`, `SILENT_CALL`
    (a handler-returned method sent as a call, incl. a `RetryMiddleware` give-up), `WEBHOOK_REPLY`, `TEARDOWN`.
  There is no `RETRY` phase. `ErrorEvent.phase` is never a runtime phase.
- **Bubbling (D48):** the executor (E-02) catches at the raising frame: the matched handler's router, or the router
  whose outer middleware / root filter / candidate filter failed. Its `errors` observer runs; on `UNHANDLED` the
  parent's runs, up to the dispatcher. The router path comes from the snapshot (zero cost without errors). A handled
  error ends the update with the error handler's return value (no further candidates).
- **Catch points (PD-04):**
  1. the routing stage (inside the `dp.update` outer chain, so inside FSM isolation) handles errors raised from
     routing;
  2. `FSMContextMiddleware` catches errors raised by `dp.update` outer middlewares that run **inside its scope**
     (after it in the chain) and dispatches them to `errors` handlers there (`phase=OUTER_MIDDLEWARE`, `router=dp`),
     then runs `close_point`, then releases the lock — the same order as a routing error;
  3. only errors raised **outside** that scope (an outer middleware before `FSMContextMiddleware`, or any outer
     middleware when FSM is off) use the dispatcher-level catch around the whole outer chain
     (`phase=OUTER_MIDDLEWARE`, `router=dp`), with `close_point` at the end of `feed_update`.
  Remove `ErrorsMiddleware`.
- **PD-05 warning:** at snapshot compile, a `RuntimeWarning` when a router has `errors` handlers but no handler routers
  beneath it (the 3.x "sibling errors router" pattern), naming the router and the fix (move to a common parent / dp).
- **Update-scope hooks for G-02 (PD-04, D112):**
  1. `on_update_start(data)` — called once in `Dispatcher.feed_update` before the outer chain; G-02 stores its scope in
     `data` under a private key;
  2. `record_escaped(exc)` — called by the executor with the exception that escaped the handler chain **before** any
     `errors` handler runs, regardless of later handling;
  3. `close_point(data, exc, *, reporter)` — called after `errors` handlers finished and **before the FSM isolation lock is
     released**: implemented as a call at the exit of `FSMContextMiddleware.__call__` (`aiogram/fsm/middleware.py`)
     when FSM is enabled, otherwise at the end of `feed_update`. It runs the release hooks registered with
     `add_release_hook(hook: Callable[[], Awaitable[None]]) -> None` — the API F-03 defines on the isolation handle and on the no-key scope object (same
     method, so one code path) — LIFO. Errors raised by a hook are passed to the `reporter` callable
     (`reporter(exc, phase)`) and never re-raised; E-12 installs `emit_runtime_error` as the reporter, so they reach
     `dp.runtime_errors` with `phase=TEARDOWN`. Until E-12 lands the default reporter logs.
  E ships these as an internal protocol with a no-op default; G-02 registers `on_update_start` / `record_escaped`
  and adds its teardown through `add_release_hook` (no separate teardown entry point).
- `DEPENDENCY` attribution: an exception raised while resolving a parameter (G-01 resolver) is tagged and reported with
  `phase=DEPENDENCY`.
- Errors handlers now see the data of the frame that raised (including `state`, since they run inside FSM) — note as
  an addition.

**Out:**
- `ErrorReason` / `e.reason` (D47; D-02, C-12). `dp.runtime_errors` observer (E-12). Depends itself (G-02).
- Decode-failure delivery (`phase=DECODE`) into `errors` (E-14 calls this machinery).

## Checklist

- [ ] `ErrorEvent` dataclass + `ErrorPhase`; re-exports kept; old pydantic `ErrorEvent` removed.
- [ ] Executor catch at each frame with correct `phase`, `router`, `handler`.
- [ ] Bubbling up the snapshot path; handled error stops routing.
- [ ] In-scope catch in `FSMContextMiddleware` (errors dispatch → `close_point` → release) for outer middlewares after
  it; dispatcher-level catch only for failures outside that scope; `ErrorsMiddleware` removed.
- [ ] PD-05 compile-time warning.
- [ ] Update-scope hook protocol (start / record_escaped / close_point) with no-op default; `FSMContextMiddleware`
  calls `close_point` before releasing the lock, `feed_update` calls it at its end when FSM is off; `close_point`
  takes a `reporter` (default: log; E-12 installs `emit_runtime_error` for `TEARDOWN`) and drains the F-03
  `add_release_hook` hooks (PD-04; this plan depends on F-03).
- [ ] Decide the policy when an `errors` handler itself raises (R17; proposed default: the new exception is **not**
  bubbled further; it propagates out of `feed_update` with the original as `__context__`, as in 3.x, and `close_point`
  still runs) — record in Notes and flag to owner.
- [ ] One `ErrorPhase` enum with the dispatch and runtime members listed in Scope (no `RETRY`); docs state that
  `ErrorEvent.phase` is never a runtime phase.
- [ ] Docs: errors page (bubbling, phases, fields, the PD-05 warning).
- [ ] Migration-registry entries (PD-13): breaking change 17 (with a checker rule matching PD-05) and `ErrorEvent`
  no longer a `TelegramObject`; changelog fragment.
- [ ] Tests: error in handler/filter/inner/outer middleware of nested routers lands in the right router with the right
  phase; sibling errors router no longer catches and warns at compile; handled error stops routing;
  `record_escaped` sees the exception even when an errors handler handles it; `close_point` runs after errors
  handlers and before the isolation lock release (assert with a fake isolation); errors-handler failure policy.

## Acceptance criteria

- Every `ErrorEvent` delivered in the test matrix has non-null `bot`, `router`, `phase`; `handler` is set from the
  `FILTER` phase onward for the candidate concerned.
- With no error, the bench (A-05 routing scenario) shows no measurable cost from bubbling (≤1% vs E-02 baseline).
- The PD-05 warning fires for the sibling pattern and not for errors handlers on a parent router.
- With a recording test scope: order is `record_escaped` → errors handlers → `close_point` → isolation release, both
  for a handler error and for an error from an outer middleware registered after `FSMContextMiddleware`; an error from
  an outer middleware before it reaches the dispatcher-level catch with `close_point` at the end of `feed_update`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| New exception classes per error | Reason enum on existing classes | D47 |
| Keep whole-tree error propagation | Sibling routers catching each other's errors; no attribution | D48 |
| Teardown after the whole update (outside isolation) | A provider could commit after the next update of the same key started | PD-04 revises D112 wording |
| Re-raise teardown errors from `feed_update` | Double reporting; teardown errors go only to `runtime_errors` | D112 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- PD-04 hook contract, shared verbatim with F-03 and G-02: F-03 owns `add_release_hook(hook: Callable[[],
  Awaitable[None]]) -> None` on the isolation handle and the no-key scope object; this plan owns the call site
  (`close_point`); G-02 registers through that method only.
- G-02 implements the scope behind the hook protocol; H-15 reads `router`/`handler`/`phase` for route diagnostics;
  E-12 receives `TEARDOWN`; E-14 delivers `DECODE`.
- F stories touching `FSMContextMiddleware` (F-02, F-04) must keep the `close_point` call at lock exit.

## Notes

- Coordinator default (reconciliation, K4): outer-middleware errors raised inside `FSMContextMiddleware`'s scope are
  dispatched to `errors` inside that scope (errors → `close_point` → release); only errors outside it use the
  dispatcher-level catch.

- Coordinator default (reconciliation, K16): one `ErrorPhase` enum; runtime phases `STARTUP`, `SHUTDOWN`, `BOT_HOOK`,
  `POLLING`, `SILENT_CALL`, `WEBHOOK_REPLY`, `TEARDOWN`; no `RETRY`.
