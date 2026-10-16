## ADDED Requirements

### Requirement: Topic refusals use Telegram's wording

A Bot API call naming a thread the forum never had SHALL fail with
`message thread not found`, and one naming a topic `deleteForumTopic` removed SHALL fail
with `TOPIC_DELETED`. A topic a test or an actor names that the chat lacks SHALL be a setup
error that lists the chat's topics, never a Telegram error.

#### Scenario: Posting into an unknown thread

- **WHEN** a handler sends a message with a thread id the forum never had
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Posting into a deleted topic

- **WHEN** a handler deletes a topic and then posts into it
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_DELETED`

#### Scenario: A test names an unknown topic

- **WHEN** a test binds an actor to a thread id the chat does not have
- **THEN** it raises `WorldLookupError` naming the topics the chat has

### Requirement: A closed topic refuses those who cannot manage topics

A message the bot sends, copies or forwards into a closed topic, or into the General topic
while it is closed or hidden, SHALL fail with `TOPIC_CLOSED` unless the bot is the chat's
owner or an administrator holding `can_manage_topics`. A refused message SHALL use no
message id. User actors SHALL NOT be refused.

#### Scenario: A member bot posts into a closed topic

- **WHEN** the bot, a plain member, sends a message into a closed topic
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_CLOSED`

#### Scenario: An administrator managing topics posts into it

- **WHEN** the bot holds `can_manage_topics` and sends into a closed topic
- **THEN** the message is stored in that topic

#### Scenario: A hidden General topic

- **WHEN** the bot, a plain member, sends a message into a forum whose General topic is
  hidden
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_CLOSED`
