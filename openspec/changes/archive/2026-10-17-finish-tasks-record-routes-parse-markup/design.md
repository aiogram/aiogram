## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

- `drain()` finds the bot's tasks as those created since the environment's first
  asynchronous entry, minus those alive then and minus the caller.

## Decisions

### D1. Waiting uses drain's set of tasks

`wait_for_tasks()` and `drain()` share `_own_tasks()`, so they agree on what is the bot's.
It also leaves out the task that made the first entry, normally the test's own: a wait or
a drain called from a child task would otherwise wait for, or cancel, the test awaiting
it. The wait repeats `asyncio.wait` on what is pending until nothing is, so a task spawned
meanwhile counts, against one deadline on the loop's clock. Failures are collected the way
`drain()` collects them and raised as `BackgroundTaskError`; `DrainedTaskError` became its
subclass so one `pytest.raises` catches both. A timeout names each task and its
coroutine's qualified name, chains the first failure if there is one, and cancels nothing.
