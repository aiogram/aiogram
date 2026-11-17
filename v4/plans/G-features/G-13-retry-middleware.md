# G-13 — Opt-in `RetryMiddleware`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [C-06](../C-butcher/C-06-overlay-schema-loader.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md), [D-04](../D-client/D-04-drop-aiofiles-input-file-replayable.md), [D-06](../D-client/D-06-request-middleware-manager.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [D-13](../D-client/D-13-raw-bot-call-raw-method.md), [E-12](../E-runtime/E-12-runtime-errors.md), [D-02](../D-client/D-02-exceptions-error-reason-restarting-removal.md), [D-03](../D-client/D-03-token-safe-network-errors.md), [D-11](../D-client/D-11-session-on-new-codec.md) |
| Blocks | [G-14](G-14-rate-limit-middleware.md), [H-07](../H-testing-observability/H-07-api-call-spans.md), [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md) |
| Gate-conditional | no |
| Decisions | D43, D39, D50, R19, PD-17, PD-25, D110 |
| Sources | [05-network.md §2.5 (D43)](../../research/05-network.md), [19 R19](../../research/19-review-resolutions.md), [codex-review.md R19](../../research/codex-review.md), [03-routing.md §5 (D50)](../../research/03-routing.md), [04-fsm.md](../../research/04-fsm.md), [plans README §1 PD-17, PD-25](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Every bot that broadcasts reimplements 429 handling. D43 ships an opt-in request middleware:
`bot.session.middleware(RetryMiddleware(max_retries=3, max_wait=30))`. It must never duplicate a send. Retry
safety therefore comes from **generated `idempotent` metadata** and user overrides, not from a `get*` name prefix
(R19).

## Scope

**In:**
- `RetryMiddleware` in `aiogram.client.session.middlewares` (3.x base: `aiogram/client/session/middlewares/base.py`
  `BaseRequestMiddleware`; manager `manager.py`).
- **429**: retried after `parameters.retry_after`, which is always safe because Telegram did not execute the
  request. If `retry_after > max_wait`, raise `TelegramRetryAfter` immediately.
- **Network errors / 5xx**: retried with `aiogram.utils.backoff.Backoff` (existing) only for methods marked
  `idempotent` in the IR (C-06 overlay, C-20 method tables), plus the user's `retry_methods=` override set.
  - **PD-25**: new methods default to non-idempotent; raw `bot.call(...)` (D-13) retries **only 429**.
  - `getUpdates` is excluded (the Poller owns it).
  - Sends are never retried on ambiguous failures.
- **Uploads** are retried only when every `InputFile` in the request is `replayable` (D-04; True for built-ins).
- **Request snapshot reuse**: attempts reuse D-10's request snapshot, so lazy text is rendered once (R19, D117) and
  the body is identical across attempts.
- **Ordering**: Retry is **outermost** among session middlewares, enforced with D-06's anchors. The rate limiter
  (G-14) sits inside and charges each attempt.
- **Per-attempt spans (PD-17)**: Retry sets `attempt` on D-06's per-call request context before each `next` call;
  inner middlewares read it there, so H-07's `API_CALL` span is per attempt, inside Retry.
- Logging on `aiogram.client` (H-01 hierarchy): one `WARNING` per retry with method, attempt and wait. The token is
  never logged (H-02 filter).

**Out:**
- `idempotent` metadata emission: C-06 / C-20.
- `InputFile.replayable`: D-04. Request snapshot: D-10. Anchors: D-06.
- Rate limiting: G-14. `API_CALL` spans: H-07.

## Checklist

- [ ] `RetryMiddleware(max_retries=3, max_wait=30, retry_methods=(), backoff=BackoffConfig(...))`.
- [ ] 429 path, network/5xx path gated by idempotent metadata, raw-call 429-only (PD-25), upload replayability gate.
- [ ] Outermost placement via D-06 anchors; raise at registration if a user anchors it inside another middleware
      (or warn; record the choice in Notes).
- [ ] Attempt number written to D-06's per-call request context (`attempt`) for PD-17.
- [ ] **"Gives up in the background" reporting path** (D50 lists "RetryMiddleware giving up in the background" for
      `dp.runtime_errors`, but a session middleware holds no dispatcher). Settled across plans: Retry only
      re-raises and adds `.attempts` to the exception; the *caller* reports it — the E-14 silent-call path (E-11 phase `SILENT_CALL`) and
      the E-16 background webhook reply (`WEBHOOK_REPLY`) call E-12's `emit_runtime_error`, which E-12 owns. There is
      no `RETRY` phase (E-11). Retry never emits itself.
- [ ] **Decide the `max_wait` vs `isolation_warn_after` default clash.** Retry's default `max_wait=30` s inside a
      handler holds the FSM isolation lock, and D110's `isolation_warn_after` default is also 30 s, so a single
      long 429 wait triggers the isolation warning. Proposed default: `max_wait=10` s; the docs explain the
      interaction and recommend `release_isolation()` (F-03) for broadcasts. Record in Notes and flag to owner.
- [ ] **Decide whether `max_wait` is per attempt or total** (R19). Proposed default: per attempt, plus an optional
      `total_wait=None`. Record in Notes.
- [ ] Docs: client page section (safe-by-default rules, idempotent list, uploads, isolation interaction).
- [ ] Tests (100% coverage of new code), with `asyncio.sleep` patched (no new test dependency):
  - 429 with retry_after below / above `max_wait`;
  - 5xx on idempotent and non-idempotent methods;
  - raw call;
  - non-replayable upload;
  - cancellation during the wait (no further attempt);
  - body identity across attempts with lazy text.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- A non-idempotent method (`sendMessage`) is **never** sent twice after a 5xx or a network error (asserted on the
  MockedBot request log). A 429 on it is retried once after `retry_after`.
- A consumed non-replayable upload is never retried; the original error propagates.
- `bot.call("unknownMethod", …)` is retried on 429 only.
- Attempt bodies are byte-identical (D-10 snapshot), including lazy text under a locale switched between attempts.
- Without the middleware installed, request behaviour is unchanged (D-15 differential cases pass untouched).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Retry safety by `get*` prefix | `getUpdates` acknowledges offsets; raw calls and custom servers not covered | R19, D43 |
| Retry on by default | Opt-in; nothing changes unless installed | D43 |
| Spans per logical call outside Retry | Owner default: per attempt | PD-17 |
| Retrying raw calls on 5xx | Unknown side effects | PD-25 |
| Retrying sends on ambiguous failure | Duplicates | D43 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs:
  - C-06 / C-20 `idempotent` flags (and `butcher check` requiring a decision for new methods, PD-25);
  - D-04 `replayable`;
  - D-06 anchors + call context;
  - D-10 request snapshot;
  - D-13 raw call;
  - E-12 `emit_runtime_error`, called by the E-14 / E-16 silent-call path on give-up (not by Retry).
- Outputs: G-14 (ordering contract), H-07 (attempt number), H-17 (toolkit `flood.py` exercises it, 14).
- Gate: this plan's own design is gate-independent; it stays blocked until its gate-conditional inputs (C-20, D-10,
  D-11, D-13) land, but those only feed the `idempotent` table, snapshot reuse and the raw-call rule. The 429 /
  backoff / ordering core can start against D-06's middleware manager on the 3.x session.

## Notes
