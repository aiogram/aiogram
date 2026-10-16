## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`.

- `drain()` finds the bot's tasks as those created since the environment's first
  asynchronous entry, minus those alive then and minus the caller.
- Route records live in trigger frames; the environment keeps only the last finished one.

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

### D2. The history keeps trigger frames

Every `_TriggerFrame` is appended to the environment's history when it opens, and so is the
frame a direct `feed_update` gets. `route_history` flattens them. Keeping frames rather
than records lets the check reason per trigger, as `assert_handled_by` does: a frame is
flagged whole when none of its records was handled, else only its records that raised. So
`member.join()`, whose service message nobody claims, passes, and a handler that raised is
caught even when another update of its trigger was handled. Every record is kept; a test's
worth of them is small.

`expect_unhandled()` marks the frame `routes` reads. It fails when that frame has nothing
to flag, so a stale call cannot hide a handled trigger, and returns what it would flag.
`assert_handled_by` needs no escape: a trigger it passes on has a handled update.

The plugin runs the check from a `pytest_runtest_call` wrapper, reading the fixture flag and
the environment from `item.funcargs`, so it fails the test rather than its teardown and is
skipped when the test already failed.
