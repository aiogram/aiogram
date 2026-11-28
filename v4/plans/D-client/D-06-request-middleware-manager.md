# D-06 — Request middleware manager: prebuilt chain, `before=`/`after=` anchors, per-call request context

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md) |
| Blocks | [D-10](D-10-request-snapshot-and-render-hook.md), [D-11](D-11-session-on-new-codec.md), [G-13](../G-features/G-13-retry-middleware.md), [G-14](../G-features/G-14-rate-limit-middleware.md), [H-07](../H-testing-observability/H-07-api-call-spans.md) |
| Gate-conditional | no |
| Decisions | D39, D43, D44, D65, R19, PD-17 |
| Sources | [05-network.md §2.3, §2.5](../../research/05-network.md), [03-routing.md §5 D39](../../research/03-routing.md), [15-observability.md §4](../../research/15-observability.md), [19 §2 R19](../../research/19-review-resolutions.md), [09-3x-quick-wins.md #11](../../research/09-3x-quick-wins.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`BaseSession.__call__` (`aiogram/client/session/base.py`) calls
`self.middleware.wrap_middlewares(self.make_request, timeout=timeout)` on **every** API call, building a chain of
`functools.partial`s (`aiogram/client/session/middlewares/manager.py`, `RequestMiddlewareManager.wrap_middlewares`).
05 §2.3: the chain is prebuilt and rebuilt only on `register`/`unregister`.

R19 requires a fixed order: `RetryMiddleware` outermost, `RateLimitMiddleware` inside it, `API_CALL` spans per
attempt inside Retry (PD-17). D39 gives session middlewares the same `before=`/`after=` anchors as router
middlewares. `RequestLogging` (`aiogram/client/session/middlewares/request_logging.py`) logs to
`aiogram.middlewares`; H-01 decides it keeps that logger for one D71 window, with no alias.

## Scope

**In:**
- `RequestMiddlewareManager`:
  - `register(middleware, *, before=None, after=None)`; anchor = a middleware class (first match) or instance.
    Anchors are resolved when the chain is (re)built; a missing anchor raises `ValueError` naming it; conflicting
    anchors raise naming the cycle (same rules as D39).
  - Chain cached; invalidated on `register`/`unregister`. `__call__`(decorator form), `Sequence` API kept.
  - Per-call `timeout` no longer bound into the cached chain via `partial`; pass it through explicitly (keeps the
    `NextRequestMiddlewareType` call shape `(bot, method)` for middlewares; see Decide item).
- **Per-call request context (owned here; PD-17):** one object per API call, created by `BaseSession.__call__` (the
  outermost entry) and alive for the whole middleware chain. It carries the per-call `timeout` and the attempt
  number `attempt: int` (starts at `1`; `RetryMiddleware` (G-13) sets it before each `next` call; inner request
  middlewares such as H-07's span middleware read it). D-10 adds its snapshot fields to the same object; it does not
  create a second carrier. Read through one public accessor (proposed `current_request_context()` in
  `aiogram.client.session`).
- `RequestLogging` keeps logging to `aiogram.middlewares` for one D71 window, as H-01 decides (no alias, no logger
  change here; H-01 owns the move and its registry entry).

**Out:**
- `RetryMiddleware`, `RateLimitMiddleware` → G-13, G-14. `API_CALL` span middleware → H-07.
- Router/dispatcher middleware anchors → E-06.
- Request snapshot fields on the per-call context → D-10. Retry policy that bumps `attempt` → G-13.

## Checklist

- [ ] Cached chain + invalidation on register/unregister.
- [ ] `before=`/`after=` anchors with D39 error rules.
- [ ] Decide the per-call carrier (the only Decide item for it; D-10 cites it): how the per-call `request_timeout`,
      `attempt` and D-10's snapshot fields reach `make_request` once the chain is cached (proposed default: a per-call
      context object held in a ContextVar set by `BaseSession.__call__` for the duration of the middleware chain and
      read by `make_request`; middleware signature `(make_request, bot, method)` unchanged) — record in Notes and flag
      to owner.
- [ ] Per-call request context with `timeout` and `attempt` (default `1`, writable by an outer middleware, readable
      by inner ones) + public accessor; D-10 extends it.
- [ ] Bench: per-call overhead with 3 middlewares, before/after (A-05 harness).
- [ ] Tests (100% coverage of new code): ordering with anchors, missing anchor, cycle, invalidation.
- [ ] Changelog fragment (`feature`: anchors). No logger change or registry entry for `aiogram.middlewares` here (H-01).

## Acceptance criteria

- `wrap_middlewares` (or its replacement) is not invoked per call when middlewares are unchanged (call-count test).
- `session.middleware.register(B(), before=A)` places `B` outside `A`; `register(C(), after=Missing)` raises at the
  next call with a message naming `Missing`.
- With Retry/RateLimit stand-ins registered in either order using anchors, the resulting order is
  Retry → RateLimit → (span) → make_request.
- An outer stand-in middleware that sets `attempt=2` and calls `next` makes an inner middleware read `attempt == 2`;
  without it the inner one reads `1`; two concurrent calls see independent contexts.
- Per-call overhead with 3 no-op middlewares is lower than the A-06 stock 3.x baseline for the same setup.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rebuild the chain per call (3.x) | Measurable per-call cost | 05 §2.3, 09 #11 |
| Numeric priorities instead of anchors | D39 chose anchors for router middlewares; one model | D39 |
| Hard-code Retry/RateLimit positions in the manager | Couples core to opt-in features | D43, D44 |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client/test_session
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: H-01 (logger hierarchy; `RequestLogging` stays on `aiogram.middlewares` per H-01).
- Outputs: anchors used by G-13, G-14, H-07; the per-call request context (attempt number: written by G-13, read by
  H-07) that D-10 extends.

## Notes

- Coordinator default (reconciliation, K6): H-01 wins — `RequestLogging` keeps `aiogram.middlewares` for one D71
  window, no alias; this plan doesn't move it.
