# H-07 — API_CALL spans (per attempt, inside Retry)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-05](H-05-trace-hook-core.md), [H-19](H-19-mockedbot-port.md), [D-02](../D-client/D-02-exceptions-error-reason-restarting-removal.md), [D-06](../D-client/D-06-request-middleware-manager.md), [G-13](../G-features/G-13-retry-middleware.md), [D-11](../D-client/D-11-session-on-new-codec.md) |
| Blocks | [H-08](H-08-otel-traces.md) |
| Gate-conditional | no |
| Decisions | D63, D39, D43, D44, D47, R19, R23, PD-17 |
| Sources | [15-observability.md §3 "Traces"](../../research/15-observability.md), [05-network.md §2.3, §2.5](../../research/05-network.md), [03-routing.md §5 "Instrumentation"](../../research/03-routing.md), [19 R19, R23](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`API_CALL` spans come from a request middleware (03 §5, 15 §3) that records method, status, `ErrorReason` and the
retry attempt. `RetryMiddleware` must stay outermost (R19), so the span middleware sits **inside** Retry and emits
**one span per attempt**, with Retry exposing the attempt number (PD-17).

## Scope

**In:**
- `TracingRequestMiddleware(tracers)` in `aiogram/client/session/middlewares/` (public), built on the D-06 request
  middleware manager and anchors.
- Placement: registered with `after=RateLimitMiddleware` when that middleware is present, and in any case inside
  `RetryMiddleware`. The span therefore measures the attempt's HTTP round-trip, not the rate-limit wait (D44 charges
  every attempt).
- Install is **idempotent** per session: sessions can be shared across bots (D45), so a second install on the same
  session is a no-op.
- Span `API_CALL` attributes:

  | Attribute | Value |
  |---|---|
  | `method` | API method name (`sendMessage`, or the raw name for `bot.call`, D96) |
  | `bot_id` | the bot's id |
  | `attempt` | D-06 per-call request context `attempt` (set by G-13); `1` when Retry isn't installed |
  | `status` | HTTP status / `error_code` as exposed by D-02/D-06 |
  | `reason` | `e.reason` (`ErrorReason` value, D47), or `None` |
  | `exception` / `result` | set as in H-05 |

- Calls go through the H-05 helper (same R23 calling rules). Tracer failures never change the request outcome or
  the exception the caller sees.

**Out:**
- Automatic install on every bot through `dp.bot_added`: H-08's `setup()` does that for OTel. Users can install the
  middleware by hand for any tracer.
- Metric recording (H-09).
- Retry/RateLimit behaviour (G-13/G-14).

## Checklist

- [ ] `TracingRequestMiddleware` with anchor placement and idempotent install.
- [ ] Read the attempt number from D-06's per-call request context (`attempt`, set by G-13's Retry; `1` without
      Retry). If D-06/G-13 expose it differently than a readable per-attempt value, stop and record it in *Notes*.
- [ ] Tests with `MockedBot` (H-19) plus `RetryMiddleware`:
  - [ ] a 429 then success gives two spans, `attempt=1` and `attempt=2`, with the 429 span carrying `status=429`
        and the exception;
  - [ ] a `TelegramBadRequest` span carries `reason`;
  - [ ] the tracer-failure matrix (H-05) leaves the request result and exception unchanged;
  - [ ] a session shared by two bots gets one middleware.
- [ ] Docs: tracing page section "API calls".
- [ ] Changelog fragment.

## Acceptance criteria

- One `API_CALL` span per HTTP attempt, nested inside the current `HANDLER` span when called from a handler, with
  `attempt` counting from 1.
- Request results and exceptions are identical with and without (failing) tracers.
- Installing twice on one session leaves exactly one tracing middleware in the chain.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One span around all attempts, outside Retry | Retry must be outermost (R19); per-attempt spans show each attempt's status | PD-17 |
| Span including the rate-limit wait | Mixes queueing with network time; the wait is visible as the gap between attempt spans | PD-17 (placement default) |
| aiohttp `TraceConfig` | Works only for `AiohttpSession`; custom sessions (D-12) would get no spans | 05 §2.3 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs:
  - D-06: request middleware manager + `before=`/`after=` anchors + per-call request context (`attempt`);
  - D-02: `ErrorReason` on exceptions and status exposure;
  - G-13: writes the attempt number into that context (PD-17).
- Output: the middleware class that H-08 installs from `dp.bot_added`.
- Gate: blocked until D-11 (gate-conditional) lands, but only the final session wiring needs it; the span middleware
  can be developed against D-06's middleware manager and per-call context.

## Notes
