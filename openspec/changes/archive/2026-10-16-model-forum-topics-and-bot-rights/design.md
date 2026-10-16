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
