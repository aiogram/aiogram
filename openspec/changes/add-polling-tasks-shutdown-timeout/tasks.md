## 1. Tests first

- [x] 1.1 Add a `polling_one_update_per_bot()` helper to `tests/test_dispatcher/test_dispatcher.py`: each bot receives one update and then a long poll that never returns, and a shutdown callback and each bot's `session.close()` record their order. Patch `Dispatcher._listen_updates` and `Dispatcher._process_update` as the existing polling tests do; no new dependencies
- [x] 1.2 A handler running when polling stops finishes before the shutdown callback and before the session closes, both for `stop_polling()` and for `_signal_stop_polling(signal.SIGTERM)`, with `tasks_concurrency_limit` of `None` and `1`; the INFO record names the number of updates
- [x] 1.3 A handler still running after the timeout (`0` and `0.05`) is cancelled, and the cancellation is handled before the shutdown callback; exactly one WARNING with the number of handlers
- [x] 1.4 Without the parameter nothing waits: shutdown and session close happen while the handler is still in `_handle_update_tasks`, and no INFO record about waiting is logged
- [x] 1.5 With `handle_as_tasks=False` the parameter has no effect: the handler is cancelled with polling and nothing waits
- [x] 1.6 A handler that awaits `dispatcher.stop_polling()` with a timeout set is not waited for, finishes after shutdown, and is back in `_handle_update_tasks` once `stop_polling()` returns
- [x] 1.7 Two bots: both handlers finish before the shutdown callback, and both sessions close after it
- [x] 1.8 `run_polling(..., tasks_shutdown_timeout=5)`: the handler finishes before shutdown instead of being cancelled when the event loop closes
- [x] 1.9 Run them on `dev-3.x` before the change: 1.2, 1.3, 1.7 and 1.8 fail; 1.4, 1.5 and 1.6 pass there by design, since they pin behaviour that must not change
- [x] 1.10 Record in the helper when the long poll of each bot is cancelled, and expect it before any handler finishes or is cancelled, so that 1.2, 1.3, 1.7 and 1.8 also fail when the wait runs while polling still fetches updates (checked by moving the wait in front of the cancelling of the polling tasks: those 8 cases fail)
- [x] 1.11 With a fixed order of events and no timing: a handler that calls `stop_polling()` while `_stop_signal` is still clear is out of `_handle_update_tasks` while it waits for shutdown, and one that calls it after `_stop_signal` is set stays in it
- [x] 1.12 A handler that calls `stop_polling()` after `_signal_stop_polling(signal.SIGTERM)` is waited for: it is cancelled when the timeout expires, before the shutdown callback, with the WARNING about one update

## 2. Implementation

- [x] 2.1 Add `Dispatcher._wait_for_handle_update_tasks(timeout)` to `aiogram/dispatcher/dispatcher.py`: return at once for `None` or an empty set; otherwise log, `asyncio.wait()` a copy of the set with the timeout, then log, cancel and await whatever is still pending
- [x] 2.2 Add `tasks_shutdown_timeout: float | None = None` to `start_polling()` after `tasks_concurrency_limit`, with a docstring entry, and call the helper after the pending polling tasks are cancelled and before `asyncio.gather(*done)`
- [x] 2.3 Add the same parameter and docstring entry to `run_polling()` and forward it to `start_polling()` by name
- [x] 2.4 In `stop_polling()`, remove `asyncio.current_task()` from `_handle_update_tasks` before setting `_stop_signal` when it is a handler task and `_stop_signal` is not set yet, and add it back once `_stopped_signal` is set
- [x] 2.5 Confirm the tests from section 1 pass, that removing either half of 2.4 makes 1.6 fail, and that removing the `_stop_signal` check makes 1.11 and 1.12 fail

## 3. Docs and changelog

- [x] 3.1 Add a "Shutdown" section to `docs/dispatcher/long_polling.rst` before "Example": the default, a `run_polling(bot, tasks_shutdown_timeout=30)` example, the order of steps on stop, stopping from a handler, `handle_as_tasks=False`, and that handling is still not exactly-once. `docs/dispatcher/dispatcher.rst` autodocs both runners and needs no edit
- [x] 3.2 Add `CHANGES/1955.feature.rst` describing the new parameter and the unchanged default, named after issue #1955
- [x] 3.3 Say in the "Shutdown" section when the wait does not apply: tasks that handlers or middlewares start themselves, SIGINT that the dispatcher does not handle (`handle_signals=False`, Windows), a second signal during the wait, and a handler that calls `stop_polling()` after polling has started to stop or through another task (`asyncio.shield()`, `asyncio.gather()`, `asyncio.wait_for()` on Python 3.10 and 3.11); give the way to stop from a handler that avoids them. No `versionadded` note until the release number is known

## 4. Quality gates

- [x] 4.1 `make lint`: `ruff check --show-fixes --preview aiogram examples`, both `mypy --native-parser` passes and `pre-commit run --all-files` pass. `ruff format --check` and the end-of-file hook flag only `tests/test_utils/test_web_app.py`, which this change does not touch
- [x] 4.2 `uv run mypy aiogram`
- [x] 4.3 `uv run pytest tests` with coverage: total stays at 100%, including the changed lines in `aiogram/dispatcher/dispatcher.py`
- [x] 4.4 Run `tests/test_dispatcher` on Python 3.10, the lowest supported version
- [x] 4.5 Build the docs and check that the new section renders without warnings

## 5. Archive

- [ ] 5.1 On archive: add the "Waiting for updates in progress on polling shutdown" requirement to `openspec/specs/event-dispatching/spec.md`
