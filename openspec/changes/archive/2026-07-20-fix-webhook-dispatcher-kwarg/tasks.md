# Tasks

## 1. Fix

- [x] 1.1 In `Dispatcher.feed_update` (`aiogram/dispatcher/dispatcher.py`),
      add `"dispatcher": self` as the weakest entry of the context dict merge
      (before `**self.workflow_data`, `**kwargs`, `"bot": bot`).

## 2. Tests (`tests/test_dispatcher/test_dispatcher.py`)

- [x] 2.1 Unit: handler and filter declaring `dispatcher` receive the
      `Dispatcher` instance via plain `feed_update` with no extra kwargs.
- [x] 2.2 Override: `feed_update(..., dispatcher=sentinel)` delivers the
      sentinel, and `Dispatcher(dispatcher=sentinel)` workflow data also wins
      over the injected instance.
- [x] 2.3 Regression (webhook path): feed an update through
      `SimpleRequestHandler` with a filter requiring `dispatcher` (MRE shape:
      FSM-state filter on `inline_query`); assert the filtered handler fires in
      both `handle_in_background` modes. Base on `mre/simulate.py`, place under
      `tests/test_webhook/`.
- [x] 2.4 Verify polling parity: same registration fed via polling-style
      kwargs (`dispatcher=dp, bots=[bot]`) selects the same handler.

## 3. Quality gates

- [x] 3.1 `uv run ruff check --show-fixes --preview aiogram examples` and
      `uv run ruff format --check --diff aiogram tests scripts examples`
- [x] 3.2 `uv run mypy aiogram`
- [x] 3.3 `uv run pytest tests` (coverage must stay 100%)

## 4. Changelog

- [x] 4.1 Add `CHANGES/1855.bugfix.rst`: webhook-fed updates now
      expose `dispatcher` to filters/handlers the same way polling does.

## 5. Cleanup

- [x] 5.1 Remove `mre/` scratch directory before the PR (or keep locally,
      never commit).
- [x] 5.2 On archive: sync the `event-dispatching` main spec and update the
      `project-webhook-handler-bugs` memory (item 3 fixed).
