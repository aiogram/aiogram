## Why

With `handle_as_tasks=True` (the default), `Dispatcher._polling` starts one task per
update, keeps it in `Dispatcher._handle_update_tasks` and goes straight on to the next
`getUpdates` call, whose higher `offset` confirms the update to Telegram. Nothing awaits
those tasks on shutdown. When polling is stopped by SIGINT/SIGTERM or by `stop_polling()`,
`start_polling()` cancels the polling tasks, runs the shutdown callbacks and closes the bot
sessions while handlers may still be running. `run_polling()` then returns from
`asyncio.run()`, which cancels whatever handlers are left.

Reproduced on 3.31.0 with a fake session: one update whose handler sleeps 0.3 s and then
calls `sendMessage`, and `stop_polling()` called at 0.05 s.

- `start_polling()`: `getUpdates(offset=2)` is sent at 0.00 s, before the handler ends.
  The shutdown callback and `session.close()` run at 0.05 s, and the handler calls
  `sendMessage` at 0.30 s, after its session was closed.
- `run_polling()`: the same order, then the handler is cancelled after `session.close()`.

Telegram does not send a confirmed update again, so the handler's work is lost half-way.
For a payment handler this means the Stars were charged and the goods were not handed
over. There is no supported way to wait for these handlers: the task set is private, and
it was added in #1331 only to keep task references from being garbage collected.

Related: #1397 asks for more control over how updates are acknowledged, so that updates
such as `successful_payment` can be handled sequentially; #919 is a closed 2.x question
about handlers being cancelled when polling stops.

## What Changes

- Add `tasks_shutdown_timeout: float | None = None` to `Dispatcher.start_polling()` and
  `Dispatcher.run_polling()`, after `tasks_concurrency_limit`. `run_polling()` forwards it.
- When it is set and `handle_as_tasks=True`, stopping polling first stops fetching updates,
  then waits up to that many seconds for the updates still being handled, of all bots, and
  only then runs the shutdown callbacks and closes the bot sessions. Handlers still running
  after the timeout are cancelled, and their cancellation is awaited before shutdown.
- The wait is logged at INFO level with the number of updates; cancelling handlers after
  the timeout is logged at WARNING level with their number.
- A handler that calls `await dispatcher.stop_polling()` in its own task, before polling
  has started to stop, is not waited for, so it does not wait for itself;
  `stop_polling()` still returns after shutdown has completed. The docs name the cases this
  does not cover and how to avoid them.
- The wait applies to `stop_polling()` and to SIGINT/SIGTERM handled by the dispatcher
  (`handle_signals=True` on an event loop with signal handlers). A cancelled
  `start_polling()` keeps shutting down without waiting, as #1635 settled.
- With `None`, the default, nothing waits, as before.

Not breaking: the default keeps the current behaviour, and the parameter is a new keyword.
The one observable difference is that a `tasks_shutdown_timeout=` keyword passed to the
runners used to land in the contextual data through `**kwargs`; see design.md.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `event-dispatching`: the long polling runner gains a requirement for waiting on updates
  still being handled when polling stops. It is added as a new requirement; "Long polling
  runner" and "Startup and shutdown hooks" stay true as written and are not restated.

## Impact

- `aiogram/dispatcher/dispatcher.py`: the new parameter and docstrings on
  `start_polling()` and `run_polling()`, a private `_wait_for_handle_update_tasks()` helper
  called by `start_polling()`, and the handler-task exclusion in `stop_polling()`.
- `tests/test_dispatcher/test_dispatcher.py`: new tests for the wait, the timeout, the
  default, `handle_as_tasks=False`, stopping from a handler, several bots and `run_polling()`.
- `docs/dispatcher/long_polling.rst`: a new "Shutdown" section.
- `CHANGES/<issue>.feature.rst`.
- No change to `_polling`, `_listen_updates`, `emit_shutdown` or the webhook module.
