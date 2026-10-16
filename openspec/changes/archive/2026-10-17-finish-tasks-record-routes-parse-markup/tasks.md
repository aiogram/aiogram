# Tasks

## 1. Waiting for background tasks

- [x] 1.1 Add `wait_for_tasks()` over drain's set of tasks, with `BackgroundTaskError` as the base of `DrainedTaskError` (design D1); verify a broadcast finishing, tasks spawned while waiting, failures before and during the wait, the timeout naming coroutines, and a wait from a child task

## 2. Route history

- [x] 2.1 Keep every trigger frame, add `route_history`, `assert_updates_handled()`, `expect_unhandled()` and the `bot_env_assert_updates_handled` fixture (design D2); verify the per-trigger rule, a swallowed error, the escape, and the plugin failing a passing test only

## 3. Parse modes

- [x] 3.1 Port TDLib's HTML, MarkdownV2 and Markdown parsers and apply them to every modeled call with the server's entities rule (design D3); verify every tag and mark, UTF-16 offsets, each error's wording, nested items, the default parse mode, and a round trip through aiogram's renderers
