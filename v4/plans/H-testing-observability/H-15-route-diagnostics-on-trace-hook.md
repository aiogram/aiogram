# H-15 — Route diagnostics on the trace hook

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-05](H-05-trace-hook-core.md), [H-06](H-06-tracing-in-executor.md), [H-14](H-14-delivery-through-runner.md), [E-11](../E-runtime/E-11-error-model-bubbling.md), [G-02](../G-features/G-02-depends-scope-teardown.md) |
| Blocks | [H-18](H-18-toolkit-docs.md), [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D54, D63, D49, D32, D111 |
| Sources | [14-testing.md D54, §3 "Rewritten", "Overrides"](../../research/14-testing.md), [03-routing.md §5 "Instrumentation", D49, "Dependencies"](../../research/03-routing.md), [19 D111](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The toolkit records which handler and router handled each update (`RouteRecord`) by registering `_RouteMiddleware`
on `dispatcher.update.outer_middleware`, and unregistering it on dispose (`environment.py`). In 4.0 that injection
is wrong for three reasons:
- it mutates the user's dispatcher;
- D111 changes which outer middlewares run;
- it can't see filters.

D54 replaces it with the official trace hook through `CallbackTracer`. D49 `ErrorEvent.handler/router/phase`
replaces error attribution guesswork.

## Scope

**In:**
- `RouteRecord` is filled from a `CallbackTracer` (H-05) on the env's dispatcher, using the `HANDLER`, `ROUTER` and
  `FILTER` spans plus `result`/`exception`.
- The environment adds the tracer to `dp.tracers` (an epoch-bumping container, PD-18) on creation and removes it on
  dispose, so no tracer leaks across tests that share a module-level dispatcher.
- Error diagnostics read `ErrorEvent.handler`, `.router` and `.phase` (D49, E-11) instead of inferring them.
- The `_RouteMiddleware` class and its register/unregister calls are deleted.
- Overrides docs: `dp.dependency_overrides` (D32, G-02) is the way to swap dependencies. `env.on(Method, …)` stays
  for Bot API responses.

**Out:**
- Span emission (H-06).
- Toolkit docs restructure (H-18).

## Checklist

- [ ] `CallbackTracer`-based recorder replacing `_RouteMiddleware`.
- [ ] Add and remove the tracer on env create/dispose. Test that no tracer remains after dispose.
- [ ] Error diagnostics from `ErrorEvent` fields.
- [ ] Tests:
  - [ ] the recorded route for a nested-router fixture equals the expected handler and router;
  - [ ] a filter-rejected candidate shows in the diagnostics;
  - [ ] an error in an inner middleware is attributed with `phase=INNER_MIDDLEWARE`;
  - [ ] a dependency override is used inside a toolkit test.
- [ ] Port `tests/test_testing/test_all_routes.py` and other route assertions.
- [ ] No changelog (internal), unless the shape of `RouteRecord` changes for users. Then add a fragment.

## Acceptance criteria

- No `outer_middleware.register` call remains in `aiogram/test/**`.
- `dp.tracers` holds no toolkit tracer after `dispose()` (test).
- Route assertions in the toolkit suite pass unchanged in meaning.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Middleware injection | Mutates the user's dispatcher, runs only where D111 allows, can't see filters | D54, D111 |
| A toolkit-private hook into the executor | The toolkit must use only public extension points (H exit gate) | milestone H |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs:
  - H-05/H-06: tracer + spans;
  - H-14: Runner delivery;
  - E-11: `ErrorEvent` fields;
  - G-02: `dependency_overrides`.

## Notes
