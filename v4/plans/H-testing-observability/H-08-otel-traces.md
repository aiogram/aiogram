# H-08 — `aiogram[otel]`: traces

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-06](H-06-tracing-in-executor.md), [H-07](H-07-api-call-spans.md), [I-07](../I-distribution/I-07-dependencies-extras-restructure.md), [E-23](../E-runtime/E-23-bot-registry.md) |
| Blocks | [H-09](H-09-otel-metrics.md) |
| Gate-conditional | no |
| Decisions | D64, D63, R23, D67–D70 |
| Sources | [15-observability.md §3](../../research/15-observability.md), [03-routing.md §5 "Instrumentation"](../../research/03-routing.md), [07-free-threading.md (watch list)](../../research/07-free-threading.md), [08-build-release.md §8 extras](../../research/08-build-release.md), [19 R23](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D64 adds an opt-in OpenTelemetry integration. The community draft (PR #1787, branch `Vitaly312/feat/otel-support`)
uses async span managers in an `AbstractTracer` and has no OTel exporter code. D63 replaced that with sync span
context managers on the shared hook. This task implements the OTel adapter for traces on top of H-05/H-06/H-07.

## Scope

**In:**
- `aiogram/contrib/otel/__init__.py`:
  `setup(dp, *, tracer_provider=None, meter_provider=None, exclude=()) -> None`. `meter_provider` is consumed by
  H-09; this plan accepts it and passes it on.
  - Appends an `OTelTracer` to `dp.tracers` (an epoch-bumping container, PD-18). Idempotent: a second `setup` on
    the same dispatcher is a no-op.
  - Registers a `dp.bot_added` handler (E-23) that installs `TracingRequestMiddleware` (H-07) on each bot's
    session. `bot_added` also fires for bots present at start.
- `opentelemetry-api` is imported **lazily** inside `aiogram.contrib.otel`. `import aiogram` never imports it, and a
  missing package gives a clear `ImportError` naming `aiogram[otel]`.
- `OTelTracer.span(kind, **attrs)` returns `tracer.start_as_current_span(name, kind=…, attributes=…)`.
  - Span names: `aiogram.update`, `aiogram.router <router>`, `aiogram.outer_middleware <qualname>`,
    `aiogram.filter <qualname>`, `aiogram.inner_middleware <qualname>`, `aiogram.handler <handler>` (the H-06
    stable name), `aiogram.api <method>`, `aiogram.teardown`.
  - OTel span kinds: `CONSUMER` for UPDATE, `CLIENT` for API_CALL, `INTERNAL` otherwise.
  - The adapter's `Span.set_attribute` converts non-primitive values: an exception becomes `record_exception` +
    ERROR status, other objects become a type name.
- `exclude=` accepts middleware classes and `SpanKind` members.
- The `otel` extra (`opentelemetry-api`, lower bound only, D70) is declared through I-07.
- Free-threading: `opentelemetry-api`'s readiness stays on the 07 watch list. No locks are added on our side.

**Out:**
- Metrics (H-09).
- SDK/exporter configuration: the user's, documented with a console-exporter example.
- The tracing core and executor wiring (H-05/H-06).

## Checklist

- [ ] `aiogram.contrib.otel` package with `setup`, `OTelTracer` and the span adapter.
- [ ] **Decide the default `exclude`** (proposed default: `SpanKind.FILTER` is excluded by default, because PR
      #1787 dropped filter spans as noise ("refactor(tracer): drop filter spans"); built-in middlewares stay
      included; `exclude=()` turns everything on). Record the decision in *Notes* and flag it to the owner.
- [ ] Tests using `opentelemetry-sdk` with `InMemorySpanExporter` (test group only):
  - [ ] the span tree for the H-06 fixture graph, with names, kinds, attributes and parent/child links;
  - [ ] an API call inside a handler nests under the handler span;
  - [ ] an exception is recorded with ERROR status and the app still sees the original exception;
  - [ ] `exclude` works for a middleware class and for a SpanKind;
  - [ ] `setup` twice gives no duplicate spans;
  - [ ] a bot added at runtime gets API spans;
  - [ ] `import aiogram` doesn't import `opentelemetry`, checked with `python -X importtime` or a `sys.modules`
        check in a subprocess.
- [ ] Docs: "OpenTelemetry" how-to (install, `setup`, exporter example, span names, `exclude`, free-threading
      note).
- [ ] Changelog fragment.

## Acceptance criteria

- With an in-memory exporter, the exported span tree for the fixture graph matches the expected names and nesting
  exactly.
- `import aiogram` with `opentelemetry` installed leaves `opentelemetry` out of `sys.modules`.
- Application results and exceptions are unchanged with the integration installed (reuse the H-06 equivalence
  test).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Async span managers / `AbstractTracer` from PR #1787 | Extra awaits per stage; D63 chose sync context managers on one shared hook | D63 |
| OTel as a core dependency | Opt-in extra only | D64, D67 |
| Chat/user ids as span attributes by default | PII and cardinality | R23 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs:
  - H-06: executor spans and stable handler names;
  - H-07: `TracingRequestMiddleware`;
  - E-23: `dp.bot_added`;
  - I-07: the `otel` extra and the test-group dependency on `opentelemetry-sdk`.
- H-09 adds metrics in the same package and reuses `setup`.

## Notes
