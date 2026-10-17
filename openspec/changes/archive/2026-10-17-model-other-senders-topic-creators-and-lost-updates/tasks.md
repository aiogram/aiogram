# Tasks

## 1. Other senders

- [x] 1.1 Declare another bot and the bots' Bot-to-Bot Communication and privacy settings, decide delivery in `_feed`, and add `Undelivered` and the service-message switch with its fixture (design D1-D3); verify each branch of the rule, captions, edits, the topic root, channels, private chats, the switch and the rights checks
- [x] 1.2 Bind an anonymous administrator, with its sender fields on messages, topic and General topic service messages and membership updates (design D4); verify the binding's refusals, a late loss of anonymity, the FSM key, topic creation and edits

## 2. Topic creators

- [x] 2.1 Take `creator=` on `add_topic` and store it on the topic and its root (design D5); verify the bot's and a user's exemptions, the default, the forms a creator is named in, and an undeclared one

## 3. Withheld updates

- [x] 3.1 Add `deliver` to every trigger that feeds an update and withhold in `_feed` (design D6); verify a topic action, a message, a join's two updates, a promotion, `create_topic()`, the G13 actors, the queries and payments, and the lost-closure recipe

## 4. Integration

- [x] 4.1 Run `make lint`, `uv run pytest tests` with `aiogram/test` at 100% coverage, and the docs build; verify all pass with no new warnings for `testing.rst`
