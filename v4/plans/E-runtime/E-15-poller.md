# E-15 — `Poller` update source

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-14](E-14-feed-paths-forward-compat-dispatch.md), [E-05](E-05-typed-observers-unknown-update.md), [D-09](../D-client/D-09-response-decoder.md), [D-11](../D-client/D-11-session-on-new-codec.md) |
| Blocks | [E-18](E-18-compat-wrappers.md), [E-19](E-19-multi-runner-free-threading-sharding.md), [G-16](../G-features/G-16-cli-run.md), [E-21](E-21-e-exit-gate.md), [E-22](E-22-single-bot-sharding.md) |
| Gate-conditional | no |
| Decisions | D21, D22, R13, D10, D116 |
| Sources | [12-runtime.md §5, §7](../../research/12-runtime.md), [19 R13](../../research/19-review-resolutions.md), [codex-review R13](../../research/codex-review.md), [10-forward-compatibility.md §3 Layer 2](../../research/10-forward-compatibility.md), [05-network.md §2.2](../../research/05-network.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The `getUpdates` loop lives in `Dispatcher._listen_updates` / `_polling` with backoff (`aiogram/utils/backoff.py`),
and a decode failure of one element fails the whole batch and stalls polling forever (10 §1; 3x-01 mitigates it on
3.x). In 4.0 it becomes a `Poller` source on the Runner: one task per bot, per-element decode, always-advancing
offset, and a defined removal sequence (R13). Delivery is best-effort, not exactly-once.

## Scope

**In:**
- `Poller(polling_timeout=10, allowed_updates=UNSET, backoff_config=DEFAULT_BACKOFF_CONFIG, handle_as_tasks=True)` in
  the runner package; implements `UpdateSource`.
- One `getUpdates` task per bot; `request_timeout = session.timeout + polling_timeout` (3.x rule in
  `_listen_updates`); today's backoff and log messages; **409 Conflict** logged as its own cause, retried with backoff,
  no automatic `deleteWebhook`.
- `allowed_updates=UNSET` resolved from the snapshot's `resolve_used_update_types()` at source start (and on
  `refresh()`); **R13 warning** once when `unknown_update` has handlers but `allowed_updates` is derived.
- Batch decode through D-09 (per-element slices, byte copies out of the batch buffer, R04); a failing element becomes a
  shell routed per E-14; the offset **always** advances past every element with a readable id. A batch whose JSON
  is malformed or an element without a readable id: backoff + `runtime_errors(phase=POLLING)`, offset unchanged
  (cannot be isolated, codex R13).
- Offset bookkeeping with distinct names: `highest_received_id`, `last_admitted_id`, `confirmed_offset`.
- **Remove a bot:** cancel its long-poll → commit with `getUpdates(offset=last_admitted_id + 1, timeout=0, limit=1)`,
  ignoring (not dispatching) whatever it returns, which stays unconfirmed → wait for its in-flight tasks up to
  `tasks_shutdown_timeout`, then cancel → `bot_removed` → close the session if owned. A failed commit is reported to
  `runtime_errors` and the removal continues (replay possible, documented).
- Polling fetch failures → `runtime_errors(phase=POLLING)`.
- Docs: polling page rewritten on Runner/Poller; best-effort delivery statement (loss/replay cases).

**Out:**
- Compat `dp.start_polling` (E-18); thread sharding (E-22); album aggregation (deferred, D116).

## Checklist

- [ ] `Poller` source with per-bot tasks, backoff, 409 handling, timeout rule.
- [ ] `allowed_updates` derivation and the R13 warning.
- [ ] Per-element decode, always-advance, unisolatable-batch handling.
- [ ] Offset bookkeeping names; removal sequence.
- [ ] Decide the offset on **stop** (12 §5 only specifies removal; 3.x redelivers the last batch after a restart)
  (proposed default: `Runner.stop` runs the same commit step for every polled bot after its long-poll is cancelled) —
  record in Notes and flag to owner.
- [ ] Decide how `handle_as_tasks=False` maps onto the Runner (proposed default: the Poller calls
  `await runner.process(bot, update)` sequentially and sends a returned method via the silent-call path, as 3.x
  `_process_update` does) — record in Notes and flag to owner.
- [ ] Changelog fragment (`feature`); migration-registry entry (PD-13) only if a user-visible default changes (e.g.
  offset commit on stop).
- [ ] Tests with MockedBot (H-19) scripted responses: poison element, malformed batch, 409, network error backoff,
  removal while tasks run (deadline and cancel), commit failure, `limit=1` result ignored.

## Acceptance criteria

- A batch of 100 with one poison element dispatches 99 updates normally, one shell, and the next `getUpdates` call
  uses `offset = last_id + 1`.
- After `remove_bot`, the recorded calls end with `getUpdates(offset=last_admitted_id+1, timeout=0, limit=1)` and no
  update returned by it is dispatched.
- No task leaks after removal or stop (`asyncio.all_tasks()` check).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Exactly-once delivery | Telegram confirms on the next call; crash/deadline can lose or replay | R13, D22 |
| Dispatch the `limit=1` commit result | It would be dispatched outside the drain and confirmed by nobody | R13 |
| Auto `deleteWebhook` on 409 | Destructive; unchanged from 3.x | 12 §5 |
| Treat decode failure as a network error (3.x) | Stalls polling forever | D10 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Gate: this plan's own design is gate-independent, but it stays blocked until D-09 and D-11 (gate-conditional) land.
  Only per-element decode and the new session path need them: the source loop, offset/commit handling, backoff and
  shutdown can start against the 3.x session and 3.x `getUpdates` decode, then switch to D-09 / D-11.
- E-18 builds `dp.start_polling` on this; E-22's ingress poller reuses the fetch loop with a hand-off admission.
- G-16 (`aiogram run polling`, `--skip-updates`) needs a `drop_pending_updates`-style start option; add it here if
  G-16 asks, otherwise G-16 calls `deleteWebhook(drop_pending_updates=True)` before start.

## Notes
