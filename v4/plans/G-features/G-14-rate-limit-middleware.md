# G-14 — Opt-in `RateLimitMiddleware`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-13](G-13-retry-middleware.md), [D-06](../D-client/D-06-request-middleware-manager.md), [D-11](../D-client/D-11-session-on-new-codec.md) |
| Blocks | [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md) |
| Gate-conditional | no |
| Decisions | D44, D45, R19, D8 |
| Sources | [05-network.md §2.5 (D44, D45)](../../research/05-network.md), [19 R19](../../research/19-review-resolutions.md), [codex-review.md R19](../../research/codex-review.md), [07-free-threading.md](../../research/07-free-threading.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Broadcast bots hit Telegram's flood limits and then sleep on 429s. D44 ships an opt-in limiter that **waits
instead of sending**, so 429s become rare. Telegram's limits are approximate and can change, so every rate is
configurable.

## Scope

**In:**
- `RateLimitMiddleware(global_rps=30, per_chat_rps=1, per_group_per_minute=20)` in
  `aiogram.client.session.middlewares`. Token buckets live **per event loop**.
- **Chat key** from the method's `chat_id`. A group/channel is detected by a negative `chat_id` or a `@username`
  string; record the rule in Notes. Methods without `chat_id` count only against the global bucket.
- **Ordering**: it sits **inside** `RetryMiddleware` (G-13) and charges **every attempt** (R19). This is enforced
  with D-06 anchors (`after=RetryMiddleware`).
- **Cancellation**: tokens reserved by a request cancelled while waiting are refunded (R19).
- **Free-threading**: buckets are per loop. A multi-thread setup (one Runner per thread, E-19) divides the limits
  explicitly, and the docs say so. A per-loop limit is not a process-wide or multi-process limit.
- Bucket **eviction**: idle per-chat buckets are dropped after a configurable TTL, so memory stays bounded.
- Logging: one `DEBUG` per wait on `aiogram.client`.

**Out:**
- Retries: G-13.
- Cross-process or Redis-backed limiting (not in D44).

## Checklist

- [ ] Token-bucket implementation (monotonic clock, async wait, no busy loop).
- [ ] Global, per-chat and per-group buckets; key extraction from `chat_id`.
- [ ] Anchor-enforced placement inside Retry.
- [ ] Refund on cancel-while-waiting.
- [ ] Idle bucket eviction (TTL, default 10 min; record in Notes).
- [ ] **Decide the bucket key when one session is shared by several bots** (D45 docs show sharing a session).
      Proposed default: buckets are keyed by `(bot.id, chat_key)`, so each bot gets its own limits; the global
      bucket is per bot, too. Record in Notes and flag to owner.
- [ ] **Decide whether `per_group_per_minute` applies to channels** (proposed default: yes, all negative ids) —
      record in Notes.
- [ ] Docs: client page section (defaults, configurability, multi-thread division, shared sessions).
- [ ] Tests (100% coverage of new code), with `asyncio.sleep` / the clock patched:
  - global cap;
  - per-chat cap;
  - group cap;
  - attempt charging with Retry;
  - cancellation refund;
  - eviction;
  - two loops in two threads keeping independent buckets.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- With patched time and bucket capacity `B` (the burst; record the default in Notes):
  - 100 sends to one private chat take ≥ `(100 − B_chat) / 1` s simulated at `per_chat_rps=1`;
  - 100 sends to 100 chats take ≥ `(100 − B_global) / 30` s at `global_rps=30`.
- With Retry + RateLimit, a request retried twice consumes three tokens.
- A request cancelled while waiting returns its token: the next request proceeds without the extra wait.
- After TTL with no traffic, the bucket map holds no per-chat entries.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Limiter outside Retry (one charge per logical call) | Retries would exceed the real rate | R19 |
| Process-wide shared buckets | Loop-bound asyncio objects; threads divide limits explicitly | D44, 07 |
| Raising instead of waiting | D44: waits instead of sending | D44 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: G-13 (ordering contract, attempt model), D-06 (anchors).
- Output: H-17 (`flood.py` in the toolkit exercises both middlewares; 14).
- Can be developed in parallel with G-13 against a stub Retry if the anchor API is ready.
- Gate: blocked until D-11 (gate-conditional) lands, but only the final session wiring needs it; development can start
  against D-06's middleware manager on the 3.x session.

## Notes
