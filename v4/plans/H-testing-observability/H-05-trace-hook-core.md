# H-05 — Trace hook core (protocol, calling rules, adapter)

| Field | Value |
|---|---|
| Status | `in-progress` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [H-06](H-06-tracing-in-executor.md), [H-07](H-07-api-call-spans.md), [H-15](H-15-route-diagnostics-on-trace-hook.md), [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D63, D54, R23, D114, PD-18, PD-31 |
| Sources | [03-routing.md §5 "Instrumentation"](../../research/03-routing.md), [15-observability.md §2–3](../../research/15-observability.md), [19 R23](../../research/19-review-resolutions.md), [codex-review.md R23](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

One official trace hook is shared by the testing toolkit, OpenTelemetry and logging (D54). It takes the form of
**sync span context managers** (D63). R23 found that arbitrary context managers can suppress or replace
application exceptions, and that several tracers need balanced exits. This task builds the pure, executor-free
core: the protocol, the calling rules and the callback adapter, with the full tracer-failure test matrix. That
matrix is half of the milestone H exit gate. It is pulled forward (PD-31) so E-02 can build its executor against
a fixed interface.

## Scope

**In:**
- Module `aiogram/dispatcher/tracing.py` with the public names re-exported from `aiogram.dispatcher`. Intended
  API:

  ```python
  class SpanKind(StrEnum): UPDATE, ROUTER, OUTER_MIDDLEWARE, FILTER, INNER_MIDDLEWARE, HANDLER, API_CALL, TEARDOWN
  class Span(Protocol):
      def set_attribute(self, key: str, value: Any) -> None: ...
  class DispatchTracer(Protocol):
      def span(self, kind: SpanKind, **attrs: Any) -> ContextManager[Span | None]: ...
  class CallbackTracer:                      # adapter: on_enter(kind, attrs) / on_exit(kind, attrs, result, exc)
  ```

- **Calling rules (R23)** live in one internal helper used by every stage, covering the E-02 executor, H-07's
  request middleware and teardown:
  1. For each tracer in order, call `tracer.span(kind, **attrs)` and then `__enter__()` **manually**. If either
     raises, log it at `exception` level on `aiogram.dispatcher` and skip that tracer; it is never exited. Exits
     happen only for tracers whose enter succeeded.
  2. Run the stage.
  3. On each non-`None` span, set `result` (a short string: `"unhandled"`, `"skip"`, `"rejected"`, or the result's
     type name) or `exception` (the exception object). A failing `set_attribute` is logged and ignored.
  4. Call `__exit__(type, value, tb)` in **reverse order**. Its return value is **ignored**; a raising `__exit__` is
     logged and the remaining exits still run.
  5. Return the stage result, or re-raise the **original** exception (identity preserved), including
     `BaseException` such as `CancelledError`. A tracer can never suppress or replace an app error.
- This plan is a pure interface (PD-31): it does not touch `dp.tracers`. The epoch-bumping `dp.tracers` container
  (PD-18) is E-03's, and H-06 integrates it with the snapshot (copied into a tuple at compile).
- Attribute keys used across the story: `update_id`, `update_type`, `bot_id`, `router`, `handler`, `middleware`,
  `filter`, `method`, `result`, `exception`. Documented as the contract for H-06/H-07/H-08.
- Free-threading: the helper holds no shared mutable state. Tracer thread safety is the user's (D114: object state
  is shared).

**Out:**
- Calling the helper from the executor and choosing the no-tracer plan (H-06).
- API_CALL spans (H-07).
- OTel (H-08).
- The `dp.tracers` epoch container (E-03) and its snapshot integration (H-06).

## Checklist

- [ ] `tracing.py`: `SpanKind`, `Span`, `DispatchTracer`, `CallbackTracer`, and the internal enter/exit helper
      (sync, no allocation beyond one small list per stage when tracers exist).
- [ ] **Decide the SpanKind gaps** (proposed default: no new kinds in 4.0. Decode failures appear on the `UPDATE`
      span as `exception` plus `phase="decode"`. `Depends` provider resolution gets no span of its own; TEARDOWN
      covers teardown. Isolation lock wait (D28/D110) is recorded as an `isolation_wait_ms` attribute on `UPDATE`.
      New kinds can be added in a 4.x minor because `SpanKind` is a `StrEnum`). Record the decision in *Notes* and
      flag it to the owner.
- [ ] Tracer-failure matrix tests, each with 1 and 3 tracers. Cases:
  - [ ] `span()` raises;
  - [ ] `__enter__` raises;
  - [ ] `__exit__` raises;
  - [ ] `__exit__` returns `True` while the stage raises (the exception still propagates);
  - [ ] `__exit__` raises a different exception (the original propagates);
  - [ ] `set_attribute` raises;
  - [ ] the stage raises `CancelledError`;
  - [ ] span returns `None`.

      Each case checks reverse exit order, that only entered tracers exit, that the original exception's identity
      is preserved, and that one log record is written per failure.
- [ ] `CallbackTracer` tests (enter/exit callbacks get kind, attrs, result/exception).
- [ ] Microbenchmark in the PR description: helper cost with 1 and 3 no-op tracers per stage.
- [ ] Docs: "Tracing" reference (protocol, calling rules, attribute keys, a `CallbackTracer` example).
- [ ] Changelog fragment (new public API).

## Acceptance criteria

- In every matrix case, the application sees exactly the exception (same object) or result it would see with no
  tracer.
- Exits happen in reverse order of successful enters. A tracer whose enter failed is never exited.
- Every tracer failure produces exactly one `aiogram.dispatcher` log record with a traceback.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Async span context managers (the shape of OTel PR #1787) | Extra awaits per stage; sync managers nest naturally and cost less | D63 |
| `with` statements / `ExitStack` | Honour a truthy `__exit__`, which lets a tracer suppress the error | R23 |
| Plain `list` for `dp.tracers` (03 §5) | A cached snapshot on the direct-feed path silently ignores a tracer added later | PD-18 |
| Middleware injection for diagnostics (the toolkit today) | Changes routing (D111 skips outer middlewares) and can't see filters | D54 |
| De-duplicating tracer failure logs | Not needed yet. Ceiling: a broken tracer logs once per stage; add rate limiting if users report floods | — |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Pulled forward (PD-31). Pure interface with no E-03 dependency: the helper and protocol merge on their own;
  `dp.tracers` (E-03's container) is wired in H-06.
- E-02 calls the helper at stage boundaries (wired in H-06). H-07 calls it from a request middleware. H-15 and the
  toolkit use `CallbackTracer`.

## Notes

- Coordinator default (reconciliation, K10): pure interface, no E-03 dependency; `dp.tracers` epoch integration is
  E-03 + H-06.
