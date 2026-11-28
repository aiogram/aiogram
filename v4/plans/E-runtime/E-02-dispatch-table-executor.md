# E-02 — Compiled `DispatchTable` and executor

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-07](../A-contracts/A-07-differential-framework.md), [A-10](../A-contracts/A-10-routing-oracle.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md) |
| Blocks | [E-03](E-03-snapshot-lifecycle.md), [E-04](E-04-router-graph-multi-parent-flags.md), [E-06](E-06-middleware-api.md), [E-07](E-07-sync-filter-execution.md), [E-09](E-09-routing-keys-compiled-rejectors.md), [E-11](E-11-error-model-bubbling.md), [F-15](../F-fsm/F-15-statefilter-state-index.md), [H-06](../H-testing-observability/H-06-tracing-in-executor.md), [E-21](E-21-e-exit-gate.md), [G-01](../G-features/G-01-param-resolver-hook.md), [G-06](../G-features/G-06-lazy-text-capture.md) |
| Gate-conditional | no (uses a Python `routing_keys` shim until E-09 / B-05) |
| Decisions | D111, D38, R09, PD-19, PD-12, D5, README breaking change 24 |
| Sources | [03-routing.md §1–§3, §5](../../research/03-routing.md), [19 D111, R09](../../research/19-review-resolutions.md), [codex-review R09, R10](../../research/codex-review.md), [plans README §1](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 3.x path rebuilds `functools.wraps` + `partial` middleware chains on every call (`MiddlewareManager.wrap_middlewares`,
≈38% of the 21.6 µs fixed path), creates a closure per router (`Router.propagate_event`), copies kwargs twice per
filter (`FilterObject.call`) and resolves the event type through an if-chain (03 §1–§2). 03 §3 replaces this with an
immutable `DispatchTable` compiled from the router tree and executed by a small loop. This plan builds the table and
executor with **3.x semantics exactly**, except the documented D111 flattening. Everything else in E (snapshot
lifecycle, rejectors, errors, Runner) plugs into it.

## Scope

**In:**
- New module (proposed `aiogram/dispatcher/table.py`, adjust if A-01 fixed another layout):
  ```
  DispatchTable(frozen)   outer_chain (prebuilt dp.update chain) · by_event: dict[str, EventPlan] · workflow_data
  EventPlan(frozen)       frames: tuple[RouterFrame, ...] (DFS order) · candidates: tuple[Candidate, ...]
  RouterFrame             router · parent frame · outer chain for this observer · root filters · candidate span
  Candidate               router path · HandlerObject · prebuilt inner chain (inherited inner middlewares)
  ```
- `compile_table(dispatcher) -> DispatchTable` — a pure function over the current router graph (DFS == 3.x
  `sub_routers` order). Chains are prebuilt once per frame / candidate.
- Executor `execute(table, bot, update, data)` replacing `Router.propagate_event` / `_propagate_event` /
  `TelegramEventObserver.trigger` on the hot path. `Dispatcher.feed_update` calls it; `Router.propagate_event` stays as
  a thin public wrapper that compiles on demand (used by scenes and tests).
- **Event type and event**: a dict keyed by update field name instead of the if-chain in `Update.event_type`; read
  through a Python `routing_keys(update)` shim (event type, event, command, text, callback data, chat type, content
  kind) cached per update. E-09 swaps the shim for B-05's Rust `update.routing_keys()`.
- **3.x data scopes, exactly (R09, D38):**
  - update scope: the dict passed to the dp.update outer chain;
  - router scope: shallow copy at router entry, `event_router` set there (as `propagate_event` does today);
  - root-filter results merged into the router scope; **`dp.update.filter(...)` root filters are checked**;
  - observer-trigger scope: one dict shared by all candidates of an observer (`handler` key set per candidate);
  - candidate-check scope: copied lazily at the first dict-returning filter, committed to the trigger scope only when
    all filters pass. A failed candidate leaves no data behind; a passed candidate followed by `SkipHandler` does.
- **D111 flatten, PD-19 rule:** a router's outer chain for the event observer is entered **iff at least one candidate in
  its subtree survives the compiled rejectors** (before E-09 lands, "survives" = has any handler for that event type).
  Inside the frame filters run as in 3.x; when every candidate fails, the frame returns `UNHANDLED` and execution
  continues with the next sibling, as `_propagate_event` does. Continuation-called-twice and short-circuit keep working.
- `SkipHandler`, `UNHANDLED`, filter-returned dicts, `flags`, DI by signature (`CallableObject` cached spec): unchanged.
- **Handler-result seam (PD-07):** right after a handler returns, and still inside its inner/outer middleware scope
  (so the i18n context set by a middleware is live), the executor passes the return value through one internal hook
  (`on_handler_result(value, data) -> value`, no-op by default). G-06 installs D-10's capture there, so a returned
  `TelegramMethod` leaves the executor already captured; nothing captures later in `runner.feed` / `runner.process`.
- The `dp.update` observer: the routing stage is the first `dp.update` handler (today `Dispatcher._listen_update`);
  user `dp.update` handlers and inner middlewares keep their 3.x order relative to it.
- Differential cases against the external 3.x oracle (PD-12: A-10 routing oracle via the A-07 harness), with a
  difference manifest entry for D111 only.
- Bench scenarios from A-05 (03 §2 shape) wired for the 4.0 side.

**Out:**
- Topology epoch, caching, Runner snapshot, `refresh()`, mutation warning (E-03).
- Multi-parent / diamond check / router flags (E-04); anchors, per-handler middlewares (E-06).
- Sync-filter mode and `F` compilation (E-07, E-08); compiled rejectors and literal/command index (E-09).
- Error bubbling, `ErrorEvent` fields, update-scope hooks (E-11). Until E-11, keep `ErrorsMiddleware` as is.
- Tracing seams (H-06 adds them on top of this executor).
- An in-tree 3.x reference interpreter: **not built** (PD-12, the oracle is the external venv in A-10; a second copy
  of 3.x semantics in-tree would itself need an oracle).

## Checklist

- [ ] `compile_table()` producing the frozen structures above; DFS order identical to 3.x.
- [ ] Prebuilt outer chain per frame and inner chain per candidate (no per-update `partial`/`wraps`).
- [ ] Dict-based event-type lookup and the Python `routing_keys` shim, cached per update.
- [ ] Executor with the four data scopes (R09) and the commit points above.
- [ ] Root filters per observer, including `dp.update.filter`.
- [ ] D111 / PD-19 frame-entry rule.
- [ ] Handler-result seam with a no-op default; test that a hook sees the return value while a ContextVar set by a
  stand-in outer middleware is still set.
- [ ] Decide when routing keys are computed (proposed default: **after the `dp.update` outer chain**, at the routing
  stage, as 3.x computes `event_type` inside `_listen_update`; so a `dp.update` outer middleware that replaces the
  `Update` still changes routing, a router-level outer middleware that replaces the event does not) — record in Notes
  and flag to owner.
- [ ] `Dispatcher.feed_update` uses the executor (compile on every call is acceptable here; caching is E-03).
- [ ] Differential cases (A-07 harness, A-10 oracle): partially successful filter chains, `False` returns, filter
  exceptions, `SkipHandler` after passed filters, inner-middleware write then `SkipHandler`, sibling routers, nested
  mutable values, router outer middleware short-circuit, continuation called twice, `dp.update` root filter.
- [ ] Difference-manifest entry for D111 (outer middleware of a router with no surviving candidate is skipped).
- [ ] Migration-registry entry (PD-13) for breaking change 24 / D111 and a changelog fragment (`removal` or `feature`
  per the 4.0 towncrier categories).
- [ ] Tests (100% coverage of the new module).

## Acceptance criteria

- Every A-10 routing case outside the manifest produces the same outcome (handler called, data seen, return value,
  exception) as the pinned 3.x venv.
- The three R09 probes from codex-review §11 reproduce 3.x results.
- A handler-result hook registered in a test is called once per handler return, inside the middleware scope, and the
  no-hook path adds no measurable cost on `routing.52-handlers`.
- An outer middleware on a router whose observer has no handlers for the event type is not called; an outer middleware
  on a router with a handler is called even when that handler's filters then fail (PD-19).
- Bench (A-04 case `routing.52-handlers`, A-05 harness — the 03 §2 scenario: dp→r1→r2→r3, 52 handlers half `Command` half `F.text ==`, 2 outer + 2 inner
  middlewares, MockedBot, 10k updates): fixed overhead (first handler matches) **≤ the A-06 optimised-3.x baseline**,
  mid/last/unhandled **≤ the A-06 optimised-3.x baseline**. The 60–90 µs target is E-09's, not this plan's.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One shared data dict for the whole update | Changes failed-candidate isolation (reproduced) | R09 |
| Keep running outer middlewares of every router the update reaches | Forbids flattening and the rejector win; documented break instead | D111 |
| Rust dispatcher | Every filter/middleware/handler is a Python awaitable; bridging costs more than the glue saved | D5, 13 §2 |
| In-tree 3.x reference path as oracle | The oracle is an external pinned 3.x venv | PD-12 |
| Enter a router's outer chain only after one of its candidates' filters passed | Outer middlewares must run before filters (they inject filter data) | PD-19 |

## Validation

```bash
make dev
uv run pytest tests -q
uv run python -m differential run --kind routing --left pypi:aiogram==<A-10 pinned 3.x version> --right path:.   # A-07 harness, A-10 oracle
make lint
uv run mypy aiogram
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.52-handlers   # A-05 harness vs the A-06 baseline
```

## Workflow notes

- Consumes: A-07 harness, A-10 routing oracle and cases, A-05/A-06 bench scenarios and baselines.
- Produces: the table/executor API every E plan builds on; E-03 caches it, E-09 adds rejectors to `RouterFrame` /
  `Candidate`, E-11 adds error frames, H-06 adds trace seams, F-15 adds the state index as a frame-skip hook.
- Keep the executor's per-stage boundaries (frame enter, root filters, candidate filters, inner chain, handler) as
  separate functions so H-06 and E-11 can attach without restructuring.

## Notes

- Coordinator default (reconciliation, K1): the PD-07 return-time capture happens at a handler-result seam in this
  executor (inside the middleware scope); G-06 installs D-10's capture there.
