# G-02 — Built-in `Depends`, per-update scope and teardown

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-01](G-01-param-resolver-hook.md), [E-11](../E-runtime/E-11-error-model-bubbling.md), [E-12](../E-runtime/E-12-runtime-errors.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [F-03](../F-fsm/F-03-release-isolation-warn-after.md) |
| Blocks | [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md), [J-01](../J-ga/J-01-feature-inventory-audit.md), [H-06](../H-testing-observability/H-06-tracing-in-executor.md), [H-15](../H-testing-observability/H-15-route-diagnostics-on-trace-hook.md) |
| Gate-conditional | no |
| Decisions | D32, D112, D49, D50, D114, PD-01, PD-04, PD-18 |
| Sources | [03-routing.md §5 "Dependencies", "Errors"](../../research/03-routing.md), [19 D112, R09, R17](../../research/19-review-resolutions.md), [codex-review.md R17](../../research/codex-review.md), [12-runtime.md §3](../../research/12-runtime.md), [plans README §1](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Today a DB session is opened by a middleware on every update, whether or not the handler needs one. `Depends` opens
a resource only for the callables that declare it. It also gives yield-teardown, test overrides and typed parameters
through `Annotated` (03 §5).

The review (R17) showed that "about 100 lines" underestimates the contract: error ownership, the rollback/commit
choice, cancellation and caching across data scopes all need definitions. D112 and PD-04 settle the main questions.
The rest are explicit *Decide* items below.

**PD-01 supersedes "Additive (4.x; can ship in 4.0 if ready)"** in 03 §5 and README D32. This plan blocks GA.

## Scope

**In:**
- `Depends(provider, *, use_cache=True)` in `aiogram.dispatcher.di`, implemented as the reference `ParamResolver`
  (G-01). Usage: `SessionDep = Annotated[Session, Depends(get_session)]`.
- **Providers**: async and sync functions, and async and sync generators. Sync providers run inline, not in a thread;
  the docs say I/O belongs in async providers. A provider's own parameters resolve the same way (by name from
  `data`, nested `Depends`). Cycles are detected at snapshot compile.
- **Per-update scope**: created at the single boundary `Dispatcher.feed_update`, which polling, webhook and custom
  sources all go through (03 §5, 12 §3). It is stored in `data` under a private key. The scope holds the cache and
  the teardown stack.
- **Cache**: per update, keyed by provider and shared by filters, handlers, middlewares and error handlers. With
  `use_cache=False` the provider is called every time.
- **Middlewares**: `await resolve(get_session, data)` (`aiogram.dispatcher.di.resolve`) shares the same cache and
  teardown. The `(handler, event, data)` signature is unchanged.
- **Teardown (D112 + PD-04)**:
  - Generators are closed in reverse setup order.
  - Teardown runs **inside the isolation scope**: after the `errors` handlers have run, before the FSM isolation lock
    (F-02) is released, and before the source marks the update done. The scope registers its teardown with
    `add_release_hook(hook: Callable[[], Awaitable[None]]) -> None` (F-03) on the update's isolation handle, or on the
    no-key scope object when the update has no FSM key; E-11's `close_point` runs the hooks. PD-04 revises 03 §5's "after the whole update /
    after all outer middlewares".
  - **Providers always see the exception (D112).** The exception that escaped the handler chain is recorded and
    thrown into every yield-provider (`athrow` / `throw`), whether or not an `errors` handler dealt with it. A
    provider that swallows it does not suppress it.
  - Teardown errors go **only** to `dp.runtime_errors` with `phase=TEARDOWN` (E-12) and are never re-raised from
    `feed_update`.
- **Resolution errors**: a provider that raises while resolving is reported through the error model (E-11) with
  `ErrorPhase.DEPENDENCY`.
- **Overrides**: `dp.dependency_overrides[get_session] = fake_session`. This is E-03's epoch-bumping mapping (PD-18),
  captured in the snapshot (D114).
- Docs: the "Dependencies" concept page, the transaction example (commit vs rollback), the test-override recipe, and
  a note that changing overrides after start needs `runner.refresh()`. The `aiogram.test` toolkit handles that itself
  (H-17).

**Out:**
- The hook protocol: G-01.
- `ErrorPhase` members, `ErrorEvent` and the `runtime_errors` observer: E-11 / E-12. This plan emits into them.
- Application-level singletons and custom scopes beyond an update. `workflow_data` covers singletons; other scopes go
  through G-01 resolvers (03 §5).
- `TEARDOWN` trace spans: H-06. This plan calls the tracer API where H-05 exposes it, if it is already merged.

## Checklist

- [ ] `Depends` + `resolve()` + `ResolveScope` implementation (cache dict, teardown `AsyncExitStack`-like stack that
      supports sync and async generators).
- [ ] Scope creation and teardown inside `feed_update`, positioned per PD-04 relative to E-11's error dispatch and
      F-02's isolation lock: teardown registered only through F-03's `add_release_hook(hook)` (same signature in
      E-11 / F-03), run by E-11's `close_point`. Add a test that asserts ordering: errors handler → teardown → lock released → source done, for a handler error and
      for an error from a `dp.update` outer middleware inside `FSMContextMiddleware`'s scope (E-11 catch point 2).
- [ ] D112: record the escaping exception, `athrow` / `throw` it into each yield-provider, and ignore suppression.
- [ ] Teardown errors → `runtime_errors` (`TEARDOWN`), never raised. Resolution errors → `DEPENDENCY`.
- [ ] `dependency_overrides` uses E-03's epoch-bumping mapping (PD-18; do not build one); applied at snapshot compile.
- [ ] Cycle detection and `use_cache` handling at snapshot compile.
- [ ] **Decide the cache key vs the 3.x data scopes** (R09 keeps four scopes: update, router copy, observer-trigger,
      candidate-check). The proposed default: the cache is **update-wide, keyed by provider only**. The first
      resolution wins whichever scope it ran in. A provider that needs router- or candidate-scoped data must use
      `use_cache=False`, and the docs say so. Record in Notes and flag to owner.
- [ ] **Decide what happens when a middleware calls `handler` twice or concurrently** (D38 allows a second call).
      The proposed default: both calls share the one update scope and cache, teardown runs once at the end, and
      concurrent resolution of the same cached provider is guarded by a per-provider `asyncio.Lock`, so the provider
      runs once. Record in Notes and flag to owner.
- [ ] **Decide cancellation semantics.** The proposed default: on `CancelledError` the scope still tears down
      (`athrow(CancelledError)`), teardown is shielded up to the Runner's `tasks_shutdown_timeout`, and the
      cancellation is re-raised afterwards. Record in Notes and flag to owner.
- [ ] **Decide how multiple teardown failures are reported.** The proposed default: one `RuntimeErrorEvent` per
      failing provider, in teardown order. No `ExceptionGroup`, and the remaining providers still close. Record in
      Notes and flag to owner.
- [ ] **Decide what a provider failure during filter matching does.** The proposed default: the update is aborted
      and reported with `phase=DEPENDENCY` and `handler=None`, bubbling from the router being matched (D48). It does
      **not** count as "filter false". Record in Notes and flag to owner.
- [ ] **Decide the definition of "flag callables"** as a resolution site. 03 §5 lists them, but 3.x flags are data,
      not callables. The proposed default: drop them from 4.0 scope, document flags as data, and mark them a 4.x
      candidate. Record in Notes and flag to owner.
- [ ] Docs pages and examples (transaction provider; per-handler resource; test override).
- [ ] Tests (100% coverage of new code), covering the R17 acceptance list: handled and unhandled handler errors,
      provider failure during matching, rollback vs commit, cancellation, multiple cleanup errors, no double reporting,
      sync generator `throw`, `use_cache=False`, nested `Depends`, cycles, overrides, `resolve()` from a middleware,
      a provider resolved by a filter of a non-matching handler (teardown still runs).
- [ ] Changelog fragment (`feature`). No migration-registry entry, because the feature is additive.

## Acceptance criteria

- A transaction provider (`yield` inside `try/except/else`) **rolls back** when the handler raises and an `errors`
  handler returns a value. It **commits** when the handler returns normally. Both are asserted in tests.
- A teardown exception appears exactly once, in `dp.runtime_errors` with `phase=TEARDOWN`. `feed_update` returns
  normally.
- Teardown completes before the isolation lock for the update's key is released: a second update for the same key
  observes the provider's teardown side effect.
- A handler without `Depends` parameters shows no regression beyond **±3%** on the pinned E-02 dispatch bench (A-05).
- A cached provider used by a filter and the handler in one update runs exactly once.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Teardown after the whole update, outside isolation | Lets the next update for the key run before cleanup; owner moved it inside | PD-04 (revises 03 §5) |
| Teardown errors re-raised from `feed_update` | Double reporting with `runtime_errors` | D112 |
| Providers see only unhandled exceptions | Transactions would commit after a handled failure | D112 |
| Sync providers in a thread | Thread hops cost ≈43 µs each; I/O belongs in async providers | 03 §5, D34 rationale |
| Built-in singleton or application scopes | `workflow_data` / `Dispatcher(**kw)` cover them; other scopes via the G-01 hook | 03 §5 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs:
  - G-01 protocols;
  - E-11 `ErrorPhase.DEPENDENCY` / `TEARDOWN` and bubbling;
  - E-12 `runtime_errors`;
  - E-14 feed paths (single scope boundary);
  - F-02 isolation lock, whose release point PD-04 hooks into;
  - F-03 `add_release_hook(hook: Callable[[], Awaitable[None]]) -> None` on the isolation handle / no-key scope
    object (the E-11 `close_point` runs the hooks).
- Outputs:
  - H-17 needs `dependency_overrides` semantics for the testing toolkit;
  - H-06 can add `TEARDOWN` spans around the teardown stack;
  - I-19 may add a heuristic checker rule for "middleware opens a resource on every update".
- Can run in parallel with the i18n lane (G-03 onward) and the CLI lane.

## Notes
