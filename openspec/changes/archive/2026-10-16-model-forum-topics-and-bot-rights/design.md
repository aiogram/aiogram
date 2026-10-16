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
