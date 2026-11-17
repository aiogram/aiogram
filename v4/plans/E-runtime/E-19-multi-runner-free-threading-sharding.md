# E-19 — Multi-Runner over one Dispatcher and free-threading

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-03](E-03-snapshot-lifecycle.md), [E-13](E-13-runner-lifecycle-bot-registry.md), [E-15](E-15-poller.md), [F-02](../F-fsm/F-02-isolation-lock-table-default-on.md), [E-23](E-23-bot-registry.md) |
| Blocks | [E-21](E-21-e-exit-gate.md), [E-22](E-22-single-bot-sharding.md) |
| Gate-conditional | no |
| Decisions | D8, D21, D114, R12, PD-06, PD-09 |
| Sources | [07-free-threading.md §1, §3, §5](../../research/07-free-threading.md), [12-runtime.md §3](../../research/12-runtime.md), [19 R12, D114](../../research/19-review-resolutions.md), [codex-review R11, R12](../../research/codex-review.md), [04-fsm.md §3](../../research/04-fsm.md), [plans README PD-06, PD-09](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D8 makes free-threaded 3.14t+ first-class. 07 §1's execution model: one process, N threads, one asyncio loop per
thread; the `Dispatcher` (each Runner on its own snapshot), routers, filters, storages and isolation are shared; `Runner`,
`Bot` + aiohttp session and Redis clients are per loop. PD-09: Redis/Mongo storages are single-loop in 4.0. This plan
builds the multi-Runner base; single-bot thread sharding (PD-06) is [E-22](E-22-single-bot-sharding.md), built on it.

## Scope

**In:**
- **Shared Dispatcher across Runners:** N Runners (one per thread/loop) over one `Dispatcher`, each with its own
  snapshot holder (E-03). Only the main-thread Runner owns signals; stopping it stops the others.
- **`dp.run_polling_threads(bot_factory, threads=N, **polling_kw)`:** starts N threads, each with a loop, a Runner and
  a `Poller`; `bot_factory()` is called per thread because aiohttp sessions are loop-bound.
  - **multi-bot mode:** the bots returned by the factory are spread across Runners (each bot polled by exactly one
    Runner, registered in that Runner's E-23 registry);
  - single-bot mode (one bot, N worker threads) is E-22's; this plan leaves the `run_polling_threads` entry point
    open for it (a mode switch E-22 fills).
- **PD-09 guard:** at Runner start, if the dispatcher's FSM storage or isolation is a Redis/Mongo implementation and
  another Runner of the same dispatcher runs on a different loop, raise a clear `RuntimeError` ("Redis/Mongo storages
  are single-loop in aiogram 4.0; use MemoryStorage or one Runner"); document multi-Runner / sharded deployments with
  Redis/Mongo as unsupported in 4.0 (cross-check F-06 Notes).
- **Free-threading race tests (3.14t, `PYTHON_GIL=0`):** concurrent `dp.feed_update` from N threads on one dispatcher;
  `runner.refresh()` under load; mutation warning raised once under contention; shared router across two dispatchers in
  two threads; shutdown of all Runners with in-flight work.
- Docs: "Running on free-threaded Python" page section: execution model, `run_polling_threads` (multi-bot), the PD-09
  limitation, per-loop objects (E-22 adds the sharding section).

**Out:**
- Single-bot sharding: ingress Poller, per-worker queues, key routing, commit semantics (E-22).
- The cross-loop isolation lock table (F-02) and MemoryStorage thread safety (F-01); free-threaded wheels and CI jobs
  (I-03) — this plan adds the tests, I-03 runs them.

## Checklist

- [ ] N Runners over one Dispatcher; main-thread signal ownership; coordinated stop.
- [ ] `run_polling_threads` multi-bot mode, with the single-bot mode left to E-22.
- [ ] PD-09 guard and docs.
- [ ] Race tests listed above, runnable on 3.14t and on the GIL build with a tiny `sys.setswitchinterval`.
- [ ] Changelog fragment (`feature`); migration-registry entry not needed (additive) unless the PD-09 error affects an
  existing pattern (then add a manual-checklist entry).

## Acceptance criteria

- Multi-bot `run_polling_threads` (4 threads, 8 bots): each bot is polled by exactly one Runner, and a clean stop of
  the main Runner stops all four with no lost in-flight update.
- Free-threaded suite passes with `PYTHON_GIL=0` and `sys._is_gil_enabled()` false after import (07 §5).
- Starting a second-loop Runner with `RedisStorage` raises the PD-09 error.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Process-wide Runner per Dispatcher | One loop per thread; `Bot` sessions are loop-bound | 07 §1 |
| Multi-loop Redis/Mongo in 4.0 | Loop-bound clients; unverified pool sharing | PD-09 |

## Validation

```bash
make dev
uv run pytest tests -q
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_runner tests/test_dispatcher -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Needs F-02's cross-loop lock table, because the isolation is shared by all Runners.
- Output: the multi-Runner base and `run_polling_threads` for E-22 (sharding); I-03 runs these tests in the
  3.14t/3.15t CI jobs.

## Notes
