# E-13 — `Runner`: lifecycle state machine, sources, task set

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-03](E-03-snapshot-lifecycle.md), [E-12](E-12-runtime-errors.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md) |
| Blocks | [E-14](E-14-feed-paths-forward-compat-dispatch.md), [E-19](E-19-multi-runner-free-threading-sharding.md), [G-16](../G-features/G-16-cli-run.md), [H-14](../H-testing-observability/H-14-delivery-through-runner.md), [E-21](E-21-e-exit-gate.md), [E-23](E-23-bot-registry.md) |
| Gate-conditional | no |
| Decisions | D21, D22, D114, R12, R13 |
| Sources | [12-runtime.md §1–§4, §8](../../research/12-runtime.md), [19 R12, R13, D114](../../research/19-review-resolutions.md), [codex-review R11, R12](../../research/codex-review.md), [07-free-threading.md §1](../../research/07-free-threading.md), [15-observability.md §4](../../research/15-observability.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`Dispatcher` (`aiogram/dispatcher/dispatcher.py`) mixes routing with loop-bound lifecycle state (`_running_lock`,
`_stop_signal`, `_stopped_signal`, `_handle_update_tasks`, signal handlers in `_signal_stop_polling`, the polling loop
in `_polling` / `_listen_updates`), and the webhook has its own lifecycle in `setup_application`
(`aiogram/webhook/aiohttp_server.py`), so startup/shutdown is emitted from two places and bots are fixed at start.
D21: one `Runner` per loop owns lifecycle, signals, in-flight tasks, concurrency limit, graceful shutdown and the bot
registry; transports become sources. R12 asks for an explicit state machine; 19 resolved only part of it, so the rest
is decided here with proposed defaults. The bot registry (add/remove semantics, `bot_added`/`bot_removed`, shared-FSM
ownership across Runners) is split out into [E-23](E-23-bot-registry.md), which plugs into this state machine.

## Scope

**In:**
- New package (proposed `aiogram/runner/`): `Runner`, `UpdateSource` protocol (the registry types are E-23's).
  ```python
  runner = Runner(dp, handle_signals=True, tasks_concurrency_limit=100, tasks_shutdown_timeout=30, **workflow_kw)
  source = runner.attach(source)            # before or after start
  await runner.add_bot(bot, source=source, close_session=True)
  async with runner: ...                    # start → serve → stop
  await runner.remove_bot(bot); await runner.refresh(); await runner.stop(); await runner.wait_closed()
  ```
- **State machine:** `created → starting → started (startup hooks done) → serving (initial bot_added done, sources
  started) → stopping → draining → closed`. Failed startup rolls back: sources already started are stopped, the
  registry's rollback hook runs (E-23 announces `bot_removed` for bots already announced), `shutdown` runs only if
  `startup` completed; the exception propagates from `start()`. The state machine exposes the two registry hook
  points E-23 fills: "announce initial bots" (between `started` and `serving`) and "de-announce bots" (in `stopping`
  and on rollback).
- `dp.startup` / `dp.shutdown` emitted exactly once per Runner, with workflow data (`Runner(dp, **kw)` merged over
  `dp.workflow_data`, as `start_polling(**kw)` does).
- **Snapshot:** the E-03 `SnapshotHolder` compiled at start; `runner.refresh()` recompiles and swaps.
- **Task set + admission core:** concurrency limit (semaphore), shutdown timeout (wait, then cancel), in-flight count
  per bot (for H-09 `aiogram.runner.inflight`). `feed`/`process` entry points and decode are E-14; this plan provides
  the task/admission primitives they use.
- **Signals:** SIGINT/SIGTERM handled once, only by a Runner on the main thread; `handle_signals=True` on another
  thread logs a warning and is ignored.
- **Per-update context:** no second ContextVar. The Runner writes its fields into H-01's per-update log-context
  object (set in `feed_update`): a `runner` attribute added to that object (bot and update id/type are H-01's own
  fields). E-03's re-entrant snapshot rule and E-12's emission read the Runner from there.
- `runtime_errors` (E-12) emission for startup/shutdown hook failures.
- Lifecycle fault-injection tests (exception and cancellation in every hook, source start failure, shutdown
  deadline).

**Out:**
- Bot registry, `add_bot` / `remove_bot`, `bot_added` / `bot_removed`, `bots` tuple, `close_session`, shared-FSM
  ownership across Runners (E-23).
- Feed/process/decode (E-14), Poller (E-15), webhook (E-16), ASGI (E-17), wrappers (E-18), multi-Runner (E-19),
  sharding (E-22).

## Checklist

- [ ] `Runner`, `UpdateSource` (`start(runner)`, `stop()`, `add_bot(bot)`, `remove_bot(bot)`), `attach`.
- [ ] State machine with rollback; `async with`, `stop()`, `wait_closed()` idempotent.
- [ ] Startup/shutdown once per Runner; registry hook points for E-23 (no-op until E-23 lands).
- [ ] Task set, semaphore, shutdown timeout, per-bot in-flight counter.
- [ ] Main-thread-only signal handling.
- [ ] Runner fields written into H-01's per-update log-context object (no new ContextVar).
- [ ] Decide sources attached after start (proposed default: started immediately; `runner.detach(source)` stops it,
  and E-23 removes its bots) — record in Notes and flag to owner.
- [ ] Decide user `CancelledError` handling inside hooks (proposed default: cancellation of `start()`/`stop()` still
  runs rollback/drain to completion, then re-raises `CancelledError`) — record in Notes and flag to owner.
- [ ] Decide whether "one Runner per loop" is enforced (R11) (proposed default: not enforced globally; at most one
  running Runner per (Dispatcher, loop) pair, `RuntimeError` otherwise) — record in Notes and flag to owner.
- [ ] Docs: new "Runner & update sources" concept page (I-10 places it), lifecycle diagram.
- [ ] Changelog fragment (`feature`).
- [ ] Tests (100% coverage), including fault injection at every state transition.

## Acceptance criteria

- Fault-injection matrix: an exception or cancellation in `startup`, each source `start`, `shutdown` and each source
  `stop` leaves the Runner `closed` with no pending tasks (checked with `asyncio.all_tasks()`) and the expected
  `runtime_errors` events (the `bot_added` / `bot_removed` cases are E-23's).
- `startup` and `shutdown` each fire exactly once per Runner whatever the number of sources and bots.
- A Runner on a non-main thread never installs signal handlers.
- Inside a handler, H-01's log-context object carries the Runner, and no other per-update ContextVar exists in
  `aiogram/runner/`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Each source owns its lifecycle | Mixed polling+webhook would emit startup/shutdown twice and duplicate signals | 12 §8 |
| Move semantics (hand-off between processes, polling↔webhook switch) | Not requested | D22 |
| Freeze leases per Runner | Snapshots need none | D114 |
| Process-wide single Runner | Two applications may share a loop (R11) | R11 |

## Validation

```bash
make dev
uv run pytest tests -q
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_runner -q
make lint
uv run mypy aiogram
```

## Workflow notes

- E-14 adds `feed`/`process` on top of the task primitives; E-15/E-16/E-17 implement `UpdateSource`; E-23 fills the
  registry hook points.
- H-14 (Testing World) implements a `WorldSource`; keep the protocol minimal and documented.
- H-01 owns the per-update log-context carrier this plan writes into; H-09 reads the in-flight counter.

## Notes
