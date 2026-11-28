# E-22 — Single-bot thread sharding (ingress Poller, per-worker queues)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-19](E-19-multi-runner-free-threading-sharding.md), [E-15](E-15-poller.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [F-04](../F-fsm/F-04-fsm-hot-paths-statefilter.md) |
| Blocks | [F-16](../F-fsm/F-16-race-suite-314t.md), [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D8, R12, PD-06, PD-09 |
| Sources | [07-free-threading.md §1, §3, §5](../../research/07-free-threading.md), [12-runtime.md §3](../../research/12-runtime.md), [19 R12](../../research/19-review-resolutions.md), [codex-review R12](../../research/codex-review.md), [04-fsm.md §3](../../research/04-fsm.md), [plans README PD-06, PD-09](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

PD-06: **single-bot thread sharding ships in 4.0**. One bot's updates are spread over N Runner threads by isolation
key, through one ingress poller, because a bot has exactly one `getUpdates` offset and competing pollers conflict
(R12, 07 §1). E-19 provides N Runners over one `Dispatcher` and `run_polling_threads`; this plan adds the single-bot
mode on top of it.

## Scope

**In:**
- **Single-bot mode of `dp.run_polling_threads(bot_factory, threads=N, **polling_kw)`** (E-19's entry point): one
  **ingress** Poller (E-15's fetch loop) for the bot in the main Runner; each fetched update is handed to a worker
  Runner chosen by its **isolation key** (the FSM `StorageKey` derived by the dispatcher's `FSMStrategy`, F-04's
  `resolve_key`), preserving per-key order.
- **Hand-off:** a **bounded** per-worker queue drained on the worker loop (`run_coroutine_threadsafe` /
  `call_soon_threadsafe`), never blocking an event-loop thread on a lock. Ingress "admitted" = accepted into a worker
  queue; the ingress awaits queue capacity (backpressure to `getUpdates`).
- **Commit semantics:** what the ingress acknowledges to Telegram on stop / bot removal (see the Decide item).
- Free-threading race tests (3.14t, `PYTHON_GIL=0`): ingress hand-off ordering per key under load; shutdown with
  in-flight work in worker queues.
- Docs: the sharding section of the "Running on free-threaded Python" page (keyless updates, queue size, PD-09 note:
  Redis/Mongo sharded deployments unsupported in 4.0, as E-19's guard enforces).

**Out:**
- N Runners over one Dispatcher, multi-bot `run_polling_threads`, the PD-09 guard (E-19).
- The cross-loop isolation lock table (F-02) and its no-deadlock race test under sharding (F-16).
- Poller offset handling for a single Runner (E-15).

## Checklist

- [ ] Ingress Poller + bounded per-worker queues + key-based routing.
- [ ] Decide where updates **without** an isolation key go (no user/chat: polls, some `chat_boost`/`purchased_paid_media`-
  style updates) (proposed default: worker chosen by `update_id % N`; ordering is not guaranteed for them, documented) —
  record in Notes and flag to owner.
- [ ] Decide the per-worker queue size and overload behaviour (proposed default: `queue_size = tasks_concurrency_limit`
  per worker, ingress awaits capacity, so a slow worker slows polling for all) — record in Notes and flag to owner.
- [ ] Decide what removal/stop commits in sharded mode (proposed default: the ingress commits
  `last_admitted_id + 1` (admitted = enqueued) after workers drained, same sequence as E-15) — record in Notes and flag
  to owner.
- [ ] Race tests above, runnable on 3.14t and on the GIL build with a tiny `sys.setswitchinterval`; expose the
  sharding harness for F-16's test 9.
- [ ] Docs section.
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`feature`); no migration-registry entry (additive).

## Acceptance criteria

- Sharded single-bot run (4 workers, 10 000 scripted updates over 500 keys): every update processed exactly once;
  per-key processing order equals `update_id` order; no lost or duplicated updates at clean shutdown.
- A worker held busy makes the ingress stop fetching once that worker's queue is full (backpressure observed with a
  fake `getUpdates`), and fetching resumes when it drains.
- Throughput: sharded run on 4 threads with a CPU-bound handler (A-04 case `routing.52-handlers` with a CPU-bound
  handler body, A-05 harness) ≥ 2.5× the single-Runner run on 3.14t (report the measured number either way in Notes).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| N competing pollers for one bot | One offset per bot; competing pollers conflict (409) | R12, 07 §1 |
| Shard by `chat_id % N` | No answer for keyless updates; not every FSM strategy keys by chat | R12 |
| Defer single-bot sharding to 4.x | Owner: ships in 4.0 | PD-06 |
| Unbounded hand-off queues | No backpressure; memory grows with a slow worker | R12 |

## Validation

```bash
make dev
uv run pytest tests/test_runner -q
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_runner tests/test_dispatcher -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Inputs: E-19 (multi-Runner base, `run_polling_threads`), E-15 (fetch loop and commit sequence), F-02 (cross-loop lock
  table, which must not deadlock across worker loops), F-04 (`resolve_key`).
- Outputs: the sharding harness F-16 reuses for its cross-loop test 9; I-03 runs these tests in the 3.14t/3.15t jobs.

## Notes
