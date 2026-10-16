## Why

A production bot that runs group games end to end on the toolkit found more places where a
test cannot see what its bot does:

- **Waiting means cancelling.** `drain()` cancels the bot's background tasks, so a results
  broadcast sent from a task of its own is stopped halfway, and nothing waits for it to end.

## What Changes

- `BotTestEnvironment.wait_for_tasks()` waits until the tasks `drain()` would cancel are done,
  cancelling none, and raises their failures as the new `BackgroundTaskError`, the base of
  `DrainedTaskError`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the requirements below.

## Impact

- **Code**: `aiogram/test/environment.py`, `errors.py`, `__init__.py`.
- **Tests**: `tests/test_testing/test_wait_for_tasks.py`.
- **Docs**: the background task sections of `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
