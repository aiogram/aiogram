# E-18 — 3.x entry points as Runner wrappers

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-15](E-15-poller.md), [E-16](E-16-webhook-core-aiohttp-sources.md) |
| Blocks | [G-16](../G-features/G-16-cli-run.md), [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D21, D24 |
| Sources | [12-runtime.md §7](../../research/12-runtime.md), [codex-review R11](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

12 §7: the 3.x `Dispatcher` entry points stay, as thin wrappers over Runner + Poller / webhook core, so existing bots
start unchanged. This removes the lifecycle code left in `aiogram/dispatcher/dispatcher.py` (`start_polling`,
`run_polling`, `stop_polling`, `_polling`, `_listen_updates`, `_process_update`, `_process_with_semaphore`,
`_wait_for_handle_update_tasks`, `_signal_stop_polling`, `_feed_webhook_update`).

## Scope

**In:**
- `dp.start_polling(*bots, polling_timeout=, handle_as_tasks=, backoff_config=, allowed_updates=, handle_signals=,
  close_bot_session=, tasks_concurrency_limit=, tasks_shutdown_timeout=, **kw)`: same signature, builds
  `Runner(dp, ...)` + `Poller(...)` with those bots and serves until stopped.
- `dp.run_polling(...)`: same plus `asyncio.Runner` / uvloop selection as today.
- `dp.stop_polling()`: stops the Runner started by **this dispatcher's** `start_polling`; `RuntimeError` if none (as
  today). No cross-loop dispatcher state: the wrapper keeps a reference to its own Runner only.
- `dp.feed_webhook_update(bot, update, **kw)`: delegates to the E-16 core.
- `dp.emit_startup(*args, **kw)` / `dp.emit_shutdown(*args, **kw)`: kept working with the 3.x signatures and data
  (workflow data merged with `kw`, as the Runner passes it), for code that drives the lifecycle by hand without a
  Runner — `tests/conftest.py` does (`await dp.emit_startup()` / `await dp.emit_shutdown()`).
- Delete the lifecycle internals listed above from `Dispatcher`.

**Out:**
- New behaviour; anything not in the 3.x signatures.

## Checklist

- [ ] Wrappers with identical signatures and defaults (compare with `inspect.signature` against the pinned 3.x venv,
  A-10/A-07 harness).
- [ ] `dp.emit_startup()` / `dp.emit_shutdown()` kept with 3.x signatures, triggering the same observers and data the
  Runner uses.
- [ ] `stop_polling` scoping; calling it from another thread uses `call_soon_threadsafe` on the Runner's loop.
- [ ] Remove the moved internals and their tests; port remaining tests to the wrappers.
- [ ] Changelog fragment (`misc`).
- [ ] Tests: start/stop, signals, `handle_as_tasks=False`, concurrency limit, shutdown timeout, `close_bot_session`.

## Acceptance criteria

- `inspect.signature` of each wrapper equals the 3.x one (test), including `emit_startup` / `emit_shutdown`.
- The `tests/conftest.py` fixture that calls `await dp.emit_startup()` / `await dp.emit_shutdown()` works unchanged and
  the registered startup/shutdown handlers each run once.
- `examples/` polling bots run unchanged in the I-20 smoke job.
- `grep -n "_listen_updates\|_running_lock\|_handle_update_tasks" aiogram/dispatcher/dispatcher.py` returns nothing.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Remove `start_polling` in favour of Runner only | Gratuitous break; wrappers are cheap | D21 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- G-16 (CLI `run polling/webhook`) builds on the Runner directly but must match these defaults.

## Notes
