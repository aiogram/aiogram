## ADDED Requirements

### Requirement: Waiting for updates in progress on polling shutdown

`Dispatcher.start_polling()` and `Dispatcher.run_polling()` SHALL accept a
`tasks_shutdown_timeout` argument, in seconds.

When it is set and `handle_as_tasks=True`, stopping polling by `stop_polling()` or by a
SIGINT/SIGTERM handled by the dispatcher SHALL stop fetching updates, SHALL then wait up to
that many seconds for the updates that are still being handled, SHALL cancel the handlers
still running after that and wait for their cancellation, and only then SHALL run shutdown
callbacks and close bot sessions.

When it is `None`, the default, shutdown SHALL NOT wait for these handlers.

#### Scenario: Handler finishes within the timeout

- **GIVEN** `tasks_shutdown_timeout=T` and a handler running when polling is stopped by `stop_polling()`, or by SIGINT or SIGTERM with `handle_signals=True`
- **WHEN** the handler finishes within `T` seconds
- **THEN** polling stops fetching updates before the wait starts, and the handler completes before any shutdown callback runs and before bot sessions are closed

#### Scenario: Handler outlives the timeout

- **GIVEN** `tasks_shutdown_timeout=T`
- **WHEN** a handler is still running `T` seconds after polling was stopped
- **THEN** it is cancelled, its cancellation is awaited before shutdown callbacks run, and a warning with the number of cancelled handlers is logged

#### Scenario: Default does not wait

- **GIVEN** `tasks_shutdown_timeout` is not passed
- **WHEN** polling stops while a handler is running
- **THEN** shutdown callbacks run and bot sessions are closed without waiting for it

#### Scenario: Handlers run inside the polling loop

- **GIVEN** `handle_as_tasks=False` and `tasks_shutdown_timeout=T`
- **WHEN** polling stops while a handler is running
- **THEN** the handler is cancelled together with polling, without waiting

#### Scenario: Handler that stops polling

- **GIVEN** `tasks_shutdown_timeout=T` and polling that is not stopping yet
- **WHEN** a handler awaits `dispatcher.stop_polling()` in its own task
- **THEN** shutdown does not wait for that handler, and `stop_polling()` returns after shutdown has completed

#### Scenario: Several bots

- **GIVEN** several bots polled by one dispatcher and `tasks_shutdown_timeout=T`
- **WHEN** polling stops
- **THEN** the handlers of every bot are awaited within one shared `T` before shutdown callbacks run and before any bot session is closed
