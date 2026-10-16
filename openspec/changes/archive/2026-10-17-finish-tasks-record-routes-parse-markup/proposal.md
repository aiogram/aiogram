## Why

A production bot that runs group games end to end on the toolkit found more places where a
test cannot see what its bot does:

- **Waiting means cancelling.** `drain()` cancels the bot's background tasks, so a results
  broadcast sent from a task of its own is stopped halfway, and nothing waits for it to end.
- **Routes are forgotten.** `routes` and `last_route` report the last trigger only, so an
  update that went nowhere in the middle of a game is gone by the end of the test.

## What Changes

- `BotTestEnvironment.wait_for_tasks()` waits until the tasks `drain()` would cancel are done,
  cancelling none, and raises their failures as the new `BackgroundTaskError`, the base of
  `DrainedTaskError`.
- `route_history` keeps every route record; `assert_updates_handled()`, opt-in by call or by
  the `bot_env_assert_updates_handled` fixture, fails on what went unhandled or raised, and
  `expect_unhandled()` marks a trigger that was meant to.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the requirements below.

## Impact

- **Code**: `aiogram/test/environment.py`, `errors.py`, `plugin.py`, `__init__.py`.
- **Tests**: `tests/test_testing/test_wait_for_tasks.py`, `test_route_history.py`.
- **Docs**: the background task and routing diagnostics sections of
  `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
