## Context

`start_polling()` runs one `_polling` task per bot plus a task waiting on `_stop_signal`,
and stops on the first one that finishes:

```python
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
for task in pending:
    # (mostly) Graceful shutdown unfinished tasks
    task.cancel()
    with suppress(CancelledError):
        await task
# Wait finished tasks to propagate unhandled exceptions
await asyncio.gather(*done)
```

Its `finally` then emits shutdown, closes the bot sessions when `close_bot_session` is set,
and sets `_stopped_signal`. Both `stop_polling()` and the SIGINT/SIGTERM handler
`_signal_stop_polling()` only set `_stop_signal`, so both reach shutdown the same way.

With `handle_as_tasks=True`, `_polling` wraps each update in a task, adds it to
`self._handle_update_tasks` with `add_done_callback(self._handle_update_tasks.discard)` and
pulls the next update. `_listen_updates` sets `offset = update.update_id + 1` as soon as the
update has been yielded, so the next `getUpdates` confirms it while its handler is still
running. The set was introduced in cad42580 (#1331, a backport of #1328) to keep task
references from being garbage collected; nothing awaits it.

With `handle_as_tasks=False`, the handler runs inside the polling task. Cancelling polling
cancels the handler at once, and since the offset is advanced only after the handler
returns, the update stays unconfirmed and Telegram sends it again on the next start.

With `tasks_concurrency_limit=N`, `_polling` awaits `semaphore.acquire()` before it creates
the task, so at most `N` tasks are in the set. An update the polling task holds at
`acquire()` is neither handled nor confirmed.

## Goals / Non-Goals

**Goals:**

- An opt-in, bounded wait for updates still being handled, before shutdown callbacks run
  and before bot sessions are closed.
- The same behaviour whether polling is stopped by a signal or by `stop_polling()`.
- No change at all for callers who do not pass the new parameter.

**Non-Goals:**

- Exactly-once handling. Updates confirmed before their handler finished can still be lost,
  and handled updates that were not confirmed can still come again.
- The webhook side. `BaseRequestHandler` keeps background tasks in
  `_background_feed_update_tasks` and never awaits them either, but its lifecycle belongs to
  aiohttp's `on_shutdown`; see Open Questions.
- Sequential handling of selected update types, which #1397 asks for.
- Changing what happens when the task running `start_polling()` is itself cancelled.
  #1635 asked for that (`start_polling()` wrapped in `asyncio.wait_for()`) and was closed as
  intended behaviour, with `stop_polling()` from a separate task recommended instead. A
  cancelled `start_polling()` runs shutdown without waiting, as before.

## Decisions

### A keyword on both runners, named `tasks_shutdown_timeout`

```python
async def start_polling(
    self,
    *bots: Bot,
    ...,
    tasks_concurrency_limit: int | None = None,
    tasks_shutdown_timeout: float | None = None,
    **kwargs: Any,
) -> None: ...
```

`run_polling()` takes the same keyword and forwards it by name, as it does for
`tasks_concurrency_limit`. The `tasks_` prefix groups the two options that apply only with
`handle_as_tasks=True`. "graceful" is avoided on purpose: the code comment above and the
"Signal handling" scenario of the spec already call today's stop graceful.

*Alternatives considered.* A `Dispatcher` constructor argument would suggest that it also
covers webhook feeding, whose shutdown runs through aiohttp's `on_shutdown` and is not
handled here. A boolean flag plus a
separate timeout adds a parameter for no gain, since `None` already means "do not wait".
Waiting without any bound would let a stuck handler hold the process until the process
manager kills it, skipping shutdown callbacks altogether.

### `None` is the default

- Today `start_polling()` returns right after shutdown, and the handlers left in the set
  keep running in the caller's event loop; in the reproduction the handler finished 0.25 s
  after `start_polling()` returned. A numeric default would make every stop of every bot
  with a long handler take up to that long, and would then cancel the handler inside
  `start_polling()`. That is a behaviour change for callers who never asked for it.
- The test suite gives no reason for another default: with the default set to `10`, all
  169 tests that existed in `tests/test_dispatcher` and `tests/test_webhook` still pass,
  and only the new test that pins the default fails.
- `tasks_concurrency_limit` was added the same way in da3e84d4 (#1670): a keyword on both
  runners whose `None` default keeps the old behaviour.
- No single value fits everyone: a useful timeout depends on how long the process manager
  waits between SIGTERM and SIGKILL.

### Wait after the polling tasks are cancelled, before `gather(*done)`

```python
for task in pending:
    task.cancel()
    with suppress(CancelledError):
        await task
# Let updates that are still being handled finish before shutdown
await self._wait_for_handle_update_tasks(timeout=tasks_shutdown_timeout)
# Wait finished tasks to propagate unhandled exceptions
await asyncio.gather(*done)
```

At this point no polling task is left, so no new `getUpdates` is sent and no new handler
task appears while waiting. The wait also runs when one bot's polling task has failed,
because its exception is re-raised only afterwards by `gather(*done)`. It is inside the
`try`, so the existing `finally` (shutdown callbacks, then session close, then
`_stopped_signal`) still runs if the wait is interrupted.

It is not in the `finally`: there it would also run when `start_polling()` itself is
cancelled from outside, at a point where the polling tasks are still alive.

### One shared budget for all bots

`_handle_update_tasks` belongs to the `Dispatcher`, not to a bot, so one
`asyncio.wait(tasks, timeout=timeout)` covers the handlers of every bot passed to the
runner. With several bots the timeout is the total wait, not a per-bot wait.

### Cancel, then await, the handlers left after the timeout

```python
_, pending = await asyncio.wait(tasks, timeout=timeout)
if not pending:
    return
loggers.dispatcher.warning(...)
for task in pending:
    task.cancel()
await asyncio.wait(pending)
```

Awaiting the cancellation lets `except CancelledError` and `finally` blocks in handlers run
before shutdown callbacks, while FSM storage and bot sessions are still open. Without it,
they would run interleaved with the shutdown callbacks and the session close, which may
close what they use. `0` cancels the handlers right away and still awaits the cancellation.
Negative values are not validated: `asyncio.wait()` treats them as `0`.

### A handler that calls `stop_polling()` is not waited for

A handler may stop polling itself (for example an admin command) with
`await dispatcher.stop_polling()`, which returns only after shutdown has completed. If its
task stayed in the set, shutdown would wait for the very task that is waiting for shutdown:
the full timeout would elapse, and the handler would then be cancelled inside its own
`stop_polling()` call. Without the exclusion, the test of this case runs into its
one-second `asyncio.wait_for()` limit and fails with `TimeoutError`.

`stop_polling()` therefore removes `asyncio.current_task()` from `_handle_update_tasks`
before setting `_stop_signal`, and adds it back once `_stopped_signal` is set. Adding it
back keeps the strong reference that #1331 introduced until the task is done, which the
done callback still takes care of. The rest of that handler runs after shutdown, as it
does today.

The exclusion is keyed on `asyncio.current_task()`, so it only covers a handler that awaits
`stop_polling()` in its own task before the wait has started; see Risks for the two cases
it misses. A context variable set in the handler task would also reach tasks the handler
starts, but it would then exclude a handler that starts `stop_polling()` in a separate task
and returns without awaiting it, which must be waited for like any other handler (the
`run_polling()` test uses that pattern), so it was not used.

### Logging

- INFO `Waiting up to %s seconds for %d update(s) to be handled` when the wait starts with
  tasks in the set.
- WARNING `%d update(s) were not handled within %s seconds, cancelling them` when the
  timeout expires.
- Nothing when the timeout is `None` or no update is being handled.

## Risks / Trade-offs

- **The keyword used to become contextual data** → On 3.31.0,
  `start_polling(bot, tasks_shutdown_timeout=5)` is accepted silently: the value goes
  through `**kwargs` into the workflow data and nothing waits. After this change the name
  is consumed by the parameter, so middlewares or handlers that read
  `data["tasks_shutdown_timeout"]` stop receiving it. `tasks_concurrency_limit` carried the
  same risk. The changelog entry names the first version that waits.
- **No exactly-once handling** → A handler cancelled after the timeout has usually had its
  update confirmed already. With `tasks_concurrency_limit`, an update can be handled in
  full during the wait without having been confirmed, and Telegram sends it again on the
  next start. The docs say that side-effecting handlers still need their own protection.
- **A handler that ignores cancellation extends shutdown past the timeout** → The await
  after `cancel()` has no bound. `asyncio.run()` teardown has the same property today.
- **`stop_polling()` from a handler after the wait has started** → If polling is already
  stopping (for example after SIGTERM) and a handler that is being waited for then calls
  `stop_polling()`, that handler is in the set being waited on: it is cancelled inside
  `stop_polling()` when the timeout expires. In a probe with a timeout of 1 s and SIGTERM
  at 0.05 s, a handler that called `stop_polling()` at 0.30 s was cancelled at 1.06 s.
- **`stop_polling()` awaited through another task** → `asyncio.shield()` and
  `asyncio.gather()` run the coroutine in a new task, and `asyncio.wait_for()` does so on
  3.10 and 3.11 but not on 3.12 and 3.13 (checked with `asyncio.current_task()`). The
  task that calls `stop_polling()` is then not the handler task, so the handler is waited
  for while it waits for shutdown, and it is cancelled when the timeout expires. A probe
  with `await asyncio.wait_for(dispatcher.stop_polling(), 5)` in a handler and a timeout of
  1 s finished shutdown at 0.05 s on Python 3.13, and on 3.10 cancelled the handler at
  1.05 s. The docs describe both cases and the way to avoid them: start `stop_polling()` in
  a task of its own and return from the handler without awaiting it.
- **Signals the dispatcher does not handle** → With `handle_signals=False`, or on Windows,
  where the event loop has no signal handlers, SIGINT does not go through
  `_signal_stop_polling()`: it raises `KeyboardInterrupt` or cancels the task running
  `start_polling()`, and shutdown runs without waiting. Seen with
  `run_polling(handle_signals=False, tasks_shutdown_timeout=5)` and SIGINT on Linux with
  Python 3.10 and 3.13: the handler was cancelled at once. The docs say that the wait needs
  `stop_polling()` or a signal the dispatcher handles.
- **A second SIGINT/SIGTERM during the wait is only logged** → `_signal_stop_polling()`
  sets an event that is already set, so Ctrl+C does not cut the wait short. See Open
  Questions.

## Migration Plan

None required. The parameter is opt-in; code that does not pass it keeps the current
behaviour. To use it, pass a timeout shorter than the process manager's grace period:

```python
dp.run_polling(bot, tasks_shutdown_timeout=30)
```

## Open Questions

- Should a second SIGINT/SIGTERM during the wait cancel the remaining handlers at once?
- The webhook runner has the same gap and belongs in its own change.
  `BaseRequestHandler._handle_request_background()` answers Telegram immediately, so the
  update counts as delivered, and the task in `_background_feed_update_tasks` is never
  awaited; `register()` appends the session close to `app.on_shutdown`, whose order relative
  to the dispatcher's shutdown callbacks depends on the order of registration. A timeout on
  `BaseRequestHandler` that waits for those tasks in an `on_shutdown` callback running
  before session close could reuse `_wait_for_handle_update_tasks()`'s approach.
- A neighbouring issue seen while testing, for a separate change: `_polling` creates the
  `_process_update()` coroutine before `await semaphore.acquire()`, so a stop during
  `acquire()` leaves a coroutine that is never awaited (a `RuntimeWarning`). Cancelling the
  task that runs `start_polling()` also leaves the `_polling` tasks running after shutdown,
  but #1635 already settled that as intended.
