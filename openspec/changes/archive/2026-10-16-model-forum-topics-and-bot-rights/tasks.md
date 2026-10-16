# Tasks

## 1. Topic errors

- [x] 1.1 Split `ChatState.topic()` (setup error) from `api_topic()` (Telegram's wording), and keep a tombstone of deleted topics (design D1); verify unknown, deleted and test-named topics

## 2. Closed topics

- [x] 2.1 Refuse the bot's sends, copies and forwards into a closed topic, or a closed or hidden General topic, without `can_manage_topics` (design D2); verify every producing method, the owner, an administrator with and without the right

## 3. Topic roots

- [x] 3.1 Give topic messages the topic's root as `reply_to_message` on every bot and actor path, never for General or over an explicit reply (design D3); verify sends, moves, service messages, actors and a handler reading the name
