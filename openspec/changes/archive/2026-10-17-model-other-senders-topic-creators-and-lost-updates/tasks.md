# Tasks

## 1. Other senders

- [x] 1.1 Declare another bot and the bots' Bot-to-Bot Communication and privacy settings, decide delivery in `_feed`, and add `Undelivered` and the service-message switch with its fixture (design D1-D3); verify each branch of the rule, captions, edits, the topic root, channels, private chats, the switch and the rights checks
- [x] 1.2 Bind an anonymous administrator, with its sender fields on messages, topic and General topic service messages and membership updates (design D4); verify the binding's refusals, a late loss of anonymity, the FSM key, topic creation and edits

## 2. Topic creators

- [x] 2.1 Take `creator=` on `add_topic` and store it on the topic and its root (design D5); verify the bot's and a user's exemptions, the default, the forms a creator is named in, and an undeclared one
