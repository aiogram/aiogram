# E-12 — `dp.runtime_errors` observer

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-11](E-11-error-model-bubbling.md) |
| Blocks | [E-13](E-13-runner-lifecycle-bot-registry.md), [G-02](../G-features/G-02-depends-scope-teardown.md), [G-13](../G-features/G-13-retry-middleware.md), [E-21](E-21-e-exit-gate.md), [H-14](../H-testing-observability/H-14-delivery-through-runner.md), [E-14](E-14-feed-paths-forward-compat-dispatch.md), [E-23](E-23-bot-registry.md) |
| Gate-conditional | no |
| Decisions | D50, D112 |
| Sources | [03-routing.md §5 "Errors" D50](../../research/03-routing.md), [19 D112](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Errors outside update handling — polling fetch failures, startup/shutdown hooks, `bot_added`/`bot_removed`, webhook
background replies, Depends teardown, a background `RetryMiddleware` giving up — are only logged in 3.x (or lost).
D50 adds one observer for them. Update-handling errors stay in `errors` (E-11).

## Scope

**In:**
- `RuntimeErrorEvent(exception, phase, bot: Bot | None, update: Update | None)` frozen dataclass, `phase` one of
  E-11's runtime `ErrorPhase` members: `STARTUP`, `SHUTDOWN`, `BOT_HOOK`, `POLLING`, `SILENT_CALL`, `WEBHOOK_REPLY`,
  `TEARDOWN` (E-11 owns the enum; there is no `RETRY` phase).
- `dp.runtime_errors` observer on `Dispatcher` only (an `EventObserver`-like observer with filters, e.g.
  `ExceptionTypeFilter`). Not routed through routers, no middlewares.
- `emit_runtime_error(dp, exc, phase, bot=None, update=None)` internal API used by E-13 (startup/shutdown/bot hooks),
  E-15 (polling fetch), E-14 (silent call of a handler-returned method), E-16 (webhook background reply), and E-11's
  `close_point` (`TEARDOWN`, G-02 hooks): this plan installs `emit_runtime_error` as `close_point`'s `reporter`. This plan owns the emit API; a `RetryMiddleware` give-up in the background
  (G-13) is **not** emitted by the middleware — Retry only re-raises (with `.attempts`), and the caller's silent-call
  path (E-14 / E-16) emits it here.
- Unhandled → logged through the H-01 hierarchy on `aiogram.runner` (the fallback logger for runtime errors), with
  the H-01 per-update log context attached when one is active. An exception inside a `runtime_errors`
  handler is only logged; no recursion.
- Included in the snapshot like other observers (epoch bump on registration).

**Out:**
- Emission sites (each owning plan adds its call).

## Checklist

- [ ] `RuntimeErrorEvent`, observer, `emit_runtime_error`.
- [ ] Install `emit_runtime_error` as E-11's `close_point` reporter; test that a failing release hook produces one
  `RuntimeErrorEvent` with `phase=TEARDOWN`.
- [ ] Logging fallback on `aiogram.runner` (H-01 hierarchy) and handler-failure logging.
- [ ] Decide how code that has no dispatcher at hand reaches `runtime_errors`, e.g. `RetryMiddleware` running in a
  session that may serve bots in several Runners (proposed default: read the Runner from H-01's per-update
  log-context object, where E-13 writes it — no second ContextVar; outside an update, emission falls back to logging
  on `aiogram.runner`) — record in Notes and flag to owner.
- [ ] Docs: errors page section.
- [ ] Changelog fragment (`feature`).
- [ ] Tests: handled/unhandled, handler raising is logged once, no recursion, filter by exception type.

## Acceptance criteria

- An exception from a `runtime_errors` handler never propagates and is logged exactly once.
- Each phase value used by an emitter in this story has a test in its owning plan (listed in Notes when done).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Route runtime errors through `errors` | No update/router context; would confuse `errors` handlers | D50 |
| Re-raise teardown errors | Double reporting | D112 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Emitters: E-13, E-14, E-15, E-16, and E-11's `close_point` through the reporter installed here (for G-02). G-13 reaches `runtime_errors` only through the
  E-14 / E-16 silent-call path. Keep `emit_runtime_error` stable once E-13 starts.

## Notes
