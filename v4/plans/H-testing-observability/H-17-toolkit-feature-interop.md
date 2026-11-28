# H-17 — Toolkit interop with 4.0 features (flood/retry, Unknown, ErrorReason, i18n)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-12](H-12-toolkit-model-api-migration.md), [H-14](H-14-delivery-through-runner.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md), [D-02](../D-client/D-02-exceptions-error-reason-restarting-removal.md), [E-05](../E-runtime/E-05-typed-observers-unknown-update.md), [G-06](../G-features/G-06-lazy-text-capture.md), [G-13](../G-features/G-13-retry-middleware.md), [G-14](../G-features/G-14-rate-limit-middleware.md), [F-03](../F-fsm/F-03-release-isolation-warn-after.md), [G-02](../G-features/G-02-depends-scope-teardown.md) |
| Blocks | [H-18](H-18-toolkit-docs.md), [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | yes |
| Decisions | D43, D44, D10, D47, D107, D117, PD-07, PD-17, PD-25 |
| Sources | [14-testing.md §3 "Flood", "Forward compatibility", "Hand-written"](../../research/14-testing.md), [05-network.md §2.5](../../research/05-network.md), [10-forward-compatibility.md](../../research/10-forward-compatibility.md), [03-routing.md D47](../../research/03-routing.md), [19 D107, D117, R19](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

14 §3 lists four interop points that only make sense once the 4.0 features exist:
- `flood.py` 429s should exercise `RetryMiddleware` / `RateLimitMiddleware`, with sleeps on the world clock or
  under looptime;
- the world can emit `Unknown…` union members and unknown update types for fuzzing (D10);
- the 85 hand-written rejections should map to `ErrorReason` (D47);
- lazy i18n text must render as it does in production (PD-07).

## Scope

**In:**
- **Flood:**
  - per-chat 429 from `flood.py` drives `RetryMiddleware` (G-13: 429 retried after `retry_after`; PD-25: raw calls
    retry only 429);
  - `RateLimitMiddleware` (G-14) waits;
  - all sleeps run on the world clock or looptime (the existing looptime recipe test), so tests stay fast;
  - an `API_CALL` per-attempt assertion is possible through H-07 when a tracer is installed.
- **Forward compatibility:**
  - actors can deliver an update whose message holds an `Unknown…` union member (C-19 classes, D107 with
    `.decode_error` where relevant);
  - actors can deliver an update of an unknown type, which routes to `router.unknown_update` (E-05). Constructed
    through `Update.from_dict` with unknown keys, not by hand-building pyclasses.
- **Rejections → `ErrorReason`:** the fake raises through the production exception mapping (D-02), so `e.reason`
  is filled. A test asserts every rejection in `rejections.py` maps to a non-`None` `ErrorReason`, or is listed in
  an explicit `UNKNOWN_TO_ERRORS_JSON` set.
- **i18n:** a world scenario with the core i18n middleware (G-03/G-06):
  - a user's `language_code` selects the locale;
  - a lazy text returned from a handler is rendered in the stored message (render step from H-12/D-10);
  - an explicit `entities` / `parse_mode` next to a lazy `Text` raises (D117).

**Out:**
- The middlewares themselves (G-13/G-14).
- Unknown decoding (C-19/E-14).
- i18n engine (G-03…G-06).

## Checklist

- [ ] Flood + Retry/RateLimit scenarios on the world clock.
- [ ] Unknown-member and unknown-update-type actor helpers (`user.send_unknown(...)` style; follow the existing
      trigger naming in `actors.py`).
- [ ] Rejection → `ErrorReason` mapping test.
- [ ] **Decide where rejection texts live** (proposed default: they stay in `aiogram/test/rejections.py`, with
      `ErrorReason` used only for mapping. Moving them into an overlay beside `errors.json` (14 §3 "may") is
      deferred). Record the decision in *Notes* and flag it to the owner.
- [ ] i18n scenario tests.
- [ ] Docs snippets for each scenario (consumed by H-18).
- [ ] Changelog fragment (new toolkit triggers).

## Acceptance criteria

- A flood scenario with `RetryMiddleware(max_retries=3)` completes with the expected number of attempts in
  ≤ 0.5 s wall time (world clock), and the handler sees the final success.
- An unknown-type update reaches an `unknown_update` handler. An `Unknown…` member is observable in a message
  handler.
- The rejection mapping test passes with the explicit unknown set reviewed in the PR.
- The i18n scenario renders the user's locale in the stored message.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Real `asyncio.sleep` in flood tests | Slow and flaky | 14 §3 |
| New exception classes for fake rejections | D47 keeps the 3.x classes plus `e.reason` | D47 |
| Building `Unknown` pyclasses by hand in the toolkit | Production decode/construct paths must be exercised | D10 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Gate-conditional through H-12.
- Inputs:
  - G-13/G-14: middlewares;
  - G-06: lazy text capture;
  - C-19: Unknown classes;
  - D-02: exception mapping;
  - E-05: `unknown_update`;
  - H-14: Runner delivery.
- Each sub-scenario can land separately if one input is late. Record the split in *Notes*.

## Notes
