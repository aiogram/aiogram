## ADDED Requirements

### Requirement: The bot's background tasks can be waited for

`wait_for_tasks()` SHALL wait, cancelling nothing, until every task the environment counts
as the bot's is done: those created since its first asynchronous entry, other than those
alive then, the caller, and the task that made that entry. A task created while waiting
SHALL be waited for too. A task that ended with an exception nobody retrieved SHALL be
raised as `BackgroundTaskError`, the base of `DrainedTaskError`, with the first chained as
its cause. At the timeout, which defaults to the environment's wait timeout, it SHALL raise
`WaitTimeoutError` naming each task still running and its coroutine, and leave them
running. It SHALL return how many tasks it waited for.

#### Scenario: A results broadcast

- **WHEN** a handler broadcasts from a task and the test waits for the bot's tasks
- **THEN** every message of the broadcast is stored, and the task was not cancelled

#### Scenario: A task that never ends

- **WHEN** the bot's task is still running at the timeout
- **THEN** `WaitTimeoutError` names it and its coroutine, and it keeps running

#### Scenario: A task that failed

- **WHEN** a bot's task raised an exception nobody retrieved
- **THEN** the wait raises `BackgroundTaskError` with that exception as its cause
