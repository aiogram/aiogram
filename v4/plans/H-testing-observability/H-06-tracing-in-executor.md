# H-06 — Tracing in the snapshot executor

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-01](H-01-logger-hierarchy.md), [H-05](H-05-trace-hook-core.md), [E-02](../E-runtime/E-02-dispatch-table-executor.md), [E-03](../E-runtime/E-03-snapshot-lifecycle.md), [G-02](../G-features/G-02-depends-scope-teardown.md), [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | [H-08](H-08-otel-traces.md), [H-15](H-15-route-diagnostics-on-trace-hook.md) |
| Gate-conditional | no |
| Decisions | D63, D114, D111, D49, R23, PD-04, PD-18 |
| Sources | [03-routing.md §3, §5 "Instrumentation"](../../research/03-routing.md), [15-observability.md §2–3](../../research/15-observability.md), [19 R23, D111, D114](../../research/19-review-resolutions.md), [codex-review.md R23, §10 "Dispatch"](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D63 promises zero cost without a tracer and one span per stage with tracers. R23 adds two requirements:
- "zero cost" must be **measured** against the same plan without hook support;
- direct `dp.feed_update` needs a defined observability contract.

This task wires the H-05 helper into the compiled routing executor (E-02) at every stage.

## Scope

**In:**
- At snapshot compile (E-03), `snapshot.tracers` is the tuple copied from `dp.tracers`. If it's **empty**, the
  compiler emits the plain plan: the same closures as with no hook support, and no per-stage `if tracers:` checks.
  Otherwise it emits wrapped stage callables that call the H-05 helper.
- Spans and their attributes:

  | Span | Attributes |
  |---|---|
  | `UPDATE`, around the whole `feed_update` | `update_id`, `update_type`, `bot_id`, plus the SpanKind-gap attributes decided in H-05 (`phase="decode"`, `isolation_wait_ms`) |
  | `ROUTER`, for each router whose outer chain is entered on the matched path (D111, PD-19) | `router` |
  | `OUTER_MIDDLEWARE` / `INNER_MIDDLEWARE`, per middleware | `middleware`, the class qualname |
  | `FILTER`, per evaluated filter | `filter`; filters the compiled rejectors skip emit nothing (README breaking change 13) |
  | `HANDLER` | `handler`, `router` |
  | `TEARDOWN`, around Depends teardown (G-02, inside the isolation scope per PD-04) | — |

- **Stable handler names** (R23), computed once at compile and shared with H-01 (`aiogram_handler`) and H-09
  (labels): `module.qualname`. `<lambda>` and `<locals>` callbacks get `module.qualname@file:lineno` from
  `__code__`, never `repr()`.
- The direct `dp.feed_update()` path uses the epoch-keyed cached snapshot (D114). It gets the same spans and log
  context. That is the R23 contract, documented.
- Writes `router`, `handler` and `phase` into the H-01 per-update log context at the same stage boundaries. This is
  an attribute write, not a span, so it is done in both plan variants.
- Benchmark on the A-05 harness. Pinned inputs: the "dispatch fixed overhead" case and the "52 handlers, F filters"
  case from the README table.
  - Variants: (a) no tracer; (b) the same commit with hook support compiled out (a test-only switch); (c) 1 and
    3 no-op tracers.
  - Threshold: (a) vs (b) median difference ≤ 1% or within the run's noise band. (c) is reported, with no
    threshold.

**Out:**
- API_CALL spans (H-07).
- OTel naming and metrics (H-08/H-09).
- Executor internals beyond the wrapping seam (E-02).
- Toolkit diagnostics (H-15).

## Checklist

- [ ] Use E-03's epoch-bumping `dp.tracers` container (PD-18; do not build one); the snapshot copies it into
      `snapshot.tracers`.
- [ ] Compile-time branch: plain plan vs traced plan, selected by `snapshot.tracers`.
- [ ] Wrap every stage listed above through the H-05 helper.
- [ ] Stable handler-name helper, used by spans and the log context.
- [ ] Log-context attribute writes (router/handler/phase) at stage boundaries.
- [ ] Tests:
  - [ ] a `CallbackTracer` records the exact span tree for a fixture graph: nested routers, outer + inner
        middleware, two candidates where the first is rejected by a filter, and a handler that raises and is
        handled by a bubbling `errors` handler (D48);
  - [ ] the direct `dp.feed_update` path produces the same tree;
  - [ ] appending a tracer after a first direct feed takes effect on the next feed (epoch bump, PD-18);
  - [ ] on a running Runner, it takes effect only after `runner.refresh()`, and the warning fires.
- [ ] Tracer-failure cases from H-05 repeated end-to-end through the executor: routing outcome and `errors`
      handling are unchanged when a tracer raises in every hook.
- [ ] Benchmark run committed as a result file next to the A-05 results. Numbers in the PR description.
- [ ] Docs: span tree diagram and the attribute table.
- [ ] Changelog fragment.

## Acceptance criteria

- With no tracer, the compiled plan contains no tracing code path, and the benchmark meets the (a) vs (b)
  threshold on both pinned cases.
- Mutating `dp.tracers` bumps the topology epoch (test through the E-03 API) and the next direct `feed_update` uses
  the traced plan.
- With a tracer, the recorded span tree for the fixture graph equals the expected tree (exact order and kinds).
- Routing outcomes and `ErrorEvent` contents are identical with and without a failing tracer.
- `aiogram_router` / `aiogram_handler` appear on log records emitted inside a handler.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| A per-stage runtime `if tracers:` check | Not zero cost. The check moves to snapshot compile | D63, R23 |
| Spans for router outer chains that D111 skips | Those chains don't run in 4.0 (flatten everything) | D111, PD-19 |
| `repr(handler)` / object ids as names | Unstable and high-cardinality (R23) | R23 |
| Reading `dp.tracers` per update | A running Runner routes on its snapshot. Changes apply on `refresh()` | D114 |

## Validation

```bash
make dev            # or maturin develop --release for the benchmark
uv run pytest tests
uv run mypy aiogram
make lint
# benchmark, release build, using the command documented by A-05 for the two pinned dispatch cases
maturin develop --release
```

## Workflow notes

- Inputs:
  - E-02: executor stage seams;
  - E-03: snapshot fields + epoch;
  - G-02: teardown stage;
  - A-05: bench harness and pinned inputs.
- If G-02 is late while everything else is ready, the owner may drop G-02 from *Depends on*. This plan then lands
  without the TEARDOWN span, and the TEARDOWN wiring is recorded as a follow-up in *Notes* for G-02's PR.
- Outputs:
  - the stable handler-name helper (H-09 labels, H-01 context);
  - span trees used by H-08 and H-15.

## Notes
