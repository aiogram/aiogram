## Context

See proposal.md for the motivation; the requirements are in
`specs/bot-testing-environment/spec.md`. This section covers only the state the design
builds on.

- `ChatState.topic()` serves both the bot's calls and the test's own lookups, and raised
  `ApiRejection` for both.
- `deleteForumTopic` removed the topic from `chat.topics` and kept no trace of it.

## Decisions

### D1. Two topic lookups

`ChatState.topic()` is the test's lookup and raises `WorldLookupError`, listing the
chat's topics. `ChatState.api_topic()` is the one the modeled methods use. It answers
`message thread not found`, or `TOPIC_DELETED` for an id in the new
`deleted_topic_ids` tombstone set that `deleteForumTopic` fills. Both texts are the
Bot API server's: the first is its own check, the second Telegram's error passed through.

### D2. One place decides where a bot's message lands

`posting_topic()` is called by `build_message` and by the copy and forward path, which
between them produce every message a method with `message_thread_id` stores. It resolves
the topic through `api_topic()` and refuses a closed one. The right is read by
`bot_has_right()`, from the bot's stored membership: the owner holds every right, an
administrator what `scoped_rights()` reports for the chat's type, anyone else nothing.

### D3. The root is filled in where a topic message is built

`TopicState.root_reply()` returns the root as `reply_to_message` unless the message
already replies to one of its chat. The Bot API server falls back to the root for a
message whose reply is external, so an `external_reply` gets the root too. It is applied
in `build_message`, in the copy and forward path after the fields a move clears and
before the request's own reply, in `service_message`, and in the actor's
`_build_message` before `fields`, so an explicit reply wins.

### D4. The bot's rights are checked where each call is modeled

Each handler calls one of `require_pin_right`, `require_restrict_right`,
`require_promote_right`, `require_send_permission` and `bot_may_delete`, after the
checks that came before it: the owner guard comes first, as in TDLib. The texts are
TDLib's (`DialogManager::can_pin_messages`, `DialogParticipantManager`,
`MessageContent.cpp`), lowercased at the first letter as the Bot API server relays them.
Since the text is Telegram's, the fix is named in the docstrings and the docs instead.

The policy is on by default. `BotTestEnvironment(enforce_bot_rights=False)`, and the
`bot_env_enforce_bot_rights` fixture, turn it off for a suite that is migrating; then
`bot_has_right` answers true, so closed topics take the bot's messages too.

Not checked: chat settings and topic management rights, granting a right the bot lacks,
a bot that has left, and user actors. A media group or a batch move is checked whole
before anything is stored; `deleteMessages` skips what it may not delete.

### D5. Turning topics off keeps them

`UserActor.set_topics(enabled)` flips `ChatState.is_forum` and nothing else, so the
topics are there when it comes back. Only the owner may, as TDLib's
`toggle_channel_is_forum` checks. Neither TDLib nor the Bot API has a message for the
switch, so no update is fed. The forum methods go through `forum_chat()`, which answers
`the chat is not a forum` as TDLib's `ForumTopicManager::is_forum` does; `createForumTopic`
no longer turns a plain supergroup into a forum, and `add_supergroup(is_forum=True)`
declares one with no topics.

**Assumption.** Telegram does not document a send with a stale `message_thread_id` once
topics are off. The Bot API server's `check_chat_access` passes no topic for a chat that
is neither a forum nor a private chat, so the toolkit stores the message untagged, and an
actor bound to a topic posts untagged too.

### D6. Flood limits are a sliding window per chat

`FloodControl` keeps the send times of each chat and checks every limit that applies to
the chat's type. A refusal's `retry_after` is the time until the oldest send that keeps
the chat over a limit leaves its window, rounded up to whole seconds, so waiting exactly
that long is enough. `handle_call` reads it after the overrides and before the handler,
and records the send once the handler succeeds. The clock is `loop.time()` plus how far
`advance_time` moved the world, so both ways of waiting count. `raise_api_error` gained
`retry_after`, which goes into the response's `parameters`, so `check_response` raises
the real `TelegramRetryAfter`.
