## Why

A production bot that runs group games end to end on the toolkit found more places where a
test cannot see what its bot does:

- **Waiting means cancelling.** `drain()` cancels the bot's background tasks, so a results
  broadcast sent from a task of its own is stopped halfway, and nothing waits for it to end.
- **Routes are forgotten.** `routes` and `last_route` report the last trigger only, so an
  update that went nowhere in the middle of a game is gone by the end of the test.
- **Markup is stored raw.** A text sent with `parse_mode` keeps its tags, so a world message
  reads `<b>Night</b>` and a bot that forgets to escape a `<` passes, while Telegram refuses
  the send.
- **Fast sleeps cost real drivers.** The documented way to skip a bot's long sleeps is
  `looptime`, which moves the loop's clock, and a real database driver's deadlines run on
  that clock and expire mid-query.

## What Changes

- `BotTestEnvironment.wait_for_tasks()` waits until the tasks `drain()` would cancel are done,
  cancelling none, and raises their failures as the new `BackgroundTaskError`, the base of
  `DrainedTaskError`.
- `route_history` keeps every route record; `assert_updates_handled()`, opt-in by call or by
  the `bot_env_assert_updates_handled` fixture, fails on what went unhandled or raised, and
  `expect_unhandled()` marks a trigger that was meant to.
- Every modeled call applies its parse modes, resolved with the bot's default, as the Bot API
  server does: ports of TDLib's HTML, MarkdownV2 and Markdown parsers produce plain text and
  entities, and broken markup fails with Telegram's `can't parse entities` description.

- A documented recipe scales the application's own sleep helper in tests and leaves the
  loop's clock real. A time control mode of the toolkit's own is deferred.

Observable behavior change, toward the Bot API: a text sent with a parse mode is stored
parsed, and broken markup or an unknown parse mode now fails the call.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the requirements below.

## Impact

- **Code**: `aiogram/test/environment.py`, `errors.py`, `plugin.py`, `__init__.py`, and the new
  `markup.py`.
- **Tests**: `tests/test_testing/test_wait_for_tasks.py`, `test_route_history.py`,
  `test_markup.py`, `test_sleep_scaling_recipe.py`.
- **Docs**: the background task, routing diagnostics and formatted text sections of
  `docs/dispatcher/testing.rst`.
- **Changelog**: folded into `CHANGES/1887.feature.rst`.
