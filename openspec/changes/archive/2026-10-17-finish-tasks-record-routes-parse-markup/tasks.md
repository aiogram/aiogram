# Tasks

## 1. Waiting for background tasks

- [x] 1.1 Add `wait_for_tasks()` over drain's set of tasks, with `BackgroundTaskError` as the base of `DrainedTaskError` (design D1); verify a broadcast finishing, tasks spawned while waiting, failures before and during the wait, the timeout naming coroutines, and a wait from a child task

## 2. Route history

- [x] 2.1 Keep every trigger frame, add `route_history`, `assert_updates_handled()`, `expect_unhandled()` and the `bot_env_assert_updates_handled` fixture (design D2); verify the per-trigger rule, a swallowed error, the escape, and the plugin failing a passing test only

## 3. Parse modes

- [x] 3.1 Port TDLib's HTML, MarkdownV2 and Markdown parsers and apply them to every modeled call with the server's entities rule (design D3); verify every tag and mark, UTF-16 offsets, each error's wording, nested items, the default parse mode, and a round trip through aiogram's renderers

## 4. Fast sleeps

- [x] 4.1 Document scaling the application's own sleep helper, and why `looptime` and real drivers clash (design D4); verify the documented code runs as written, fast, with the loop's clock real

## 5. Group permissions

- [x] 5.1 Give a group or a supergroup Telegram's default permissions, overridable per chat, and read them everywhere the bot's sends are checked (design D5); verify the default's values, getChat, the override, a hand-built spec, private chats and channels, and the enforcement and restriction paths

## 6. Runtime additions

- [x] 6.1 Add users and chats to a running environment through the blueprint's builders (design D6); verify the shapes against declared ones, members by spec, actor and id, ids and collisions, and a shared blueprint left alone

## 7. Bot commands

- [x] 7.1 Mark the commands in an actor's text and caption as TDLib's matcher does, without overriding explicit entities (design D7); verify the rule's every branch, UTF-16 offsets, edits, captions, every chat kind, and that the bot's sends are untouched

## 8. Integration

- [x] 8.1 Run `make lint`, `uv run pytest tests` with `aiogram/test` at 100% coverage, and the docs build; verify all pass with no new warnings for `testing.rst`
