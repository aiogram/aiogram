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

### Requirement: A topic message replies to the topic's root

A message stored in a forum topic other than General that replies to no message of its
chat SHALL carry the topic's `forum_topic_created` service message as its
`reply_to_message`, and SHALL be marked as a topic message. This SHALL hold for the bot's
sends, copies, forwards and topic service messages and for messages a user actor sends. An
explicit reply SHALL keep its own target, and a reply in another chat SHALL still carry the
root.

#### Scenario: A handler reads the topic name

- **WHEN** an actor bound to a topic sends a message
- **THEN** the handler receives it with `reply_to_message.forum_topic_created` naming the
  topic

#### Scenario: An explicit reply keeps its target

- **WHEN** the bot replies to a message inside a topic
- **THEN** the stored message replies to that message, not to the root

#### Scenario: The General topic has no root

- **WHEN** the bot sends a message into the General topic of a forum
- **THEN** the stored message replies to nothing

### Requirement: The bot's own calls are checked against its rights

Unless the environment is built with `enforce_bot_rights=False`, a call the bot makes into
a group, a supergroup or a channel SHALL fail with Telegram's wording when the bot's
standing there does not allow it. Pinning and unpinning SHALL take `can_pin_messages`, or
`can_edit_messages` in a channel. Banning, unbanning and restricting SHALL take
`can_restrict_members`, and promoting `can_promote_members`. Deleting someone else's message
SHALL take administrator status in a basic group and `can_delete_messages` elsewhere. A
send, copy or forward by a bot that is not an administrator SHALL take the chat's permission
for that kind of message, narrowed by the bot's own restriction, and posting into a channel
SHALL take `can_post_messages`. The owner SHALL hold every right. Private chats and user
actors SHALL NOT be checked. With `enforce_bot_rights=False`, the bot SHALL hold every right.

#### Scenario: A member bot pins

- **WHEN** the bot, a plain member of a supergroup, pins a message
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to manage pinned messages in the chat`

#### Scenario: A member bot bans

- **WHEN** the bot, a plain member of a supergroup, bans a user
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to restrict/unrestrict chat member`, and the user stays

#### Scenario: A member bot sends into a silenced chat

- **WHEN** the chat's permissions forbid text and the bot, a plain member, sends text
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to send text messages to the chat`, while a user actor's message in
  the same chat is still delivered

#### Scenario: Opting out

- **WHEN** the environment is built with `enforce_bot_rights=False`
- **THEN** the same bot pins, bans and sends as if it held every right

### Requirement: The owner can turn a forum's topics off and on

A user actor who owns a supergroup SHALL be able to turn its topics off and on. No update
SHALL be delivered for it. Turning topics off SHALL keep them, and turning them on again
SHALL restore them as they were. While topics are off, the forum methods SHALL fail with
`the chat is not a forum`, and a message the bot sends with a thread id SHALL be stored
without one, which is an assumption the Bot API does not document. A blueprint SHALL be
able to declare a supergroup a forum before it has any topic. Anyone but the owner, or a
chat other than a supergroup, SHALL be a setup error.

#### Scenario: A stale thread id after topics are off

- **WHEN** the owner turns topics off and the bot sends into a former topic's thread id
- **THEN** the message is stored in the chat with no thread id, not as a topic message

#### Scenario: Turning topics on again

- **WHEN** the owner turns topics back on
- **THEN** the former topics exist again, and a message sent into one is tagged with it

#### Scenario: Someone else tries

- **WHEN** a member who is not the owner turns topics off
- **THEN** the trigger raises `WorldLookupError`, and the chat is still a forum

### Requirement: Flood limits can be modeled per chat

An environment built with `rate_limits` SHALL refuse a message-producing call into a chat
that is over a limit with error 429, `Too Many Requests: retry after N`, and a
`TelegramRetryAfter` whose `retry_after` is the whole seconds until a send into that chat is
allowed. The default limits SHALL be one message per second in any chat and 20 per minute
in a group or supergroup, counted for the whole chat across its topics. A call SHALL be
counted once it succeeds, a media group or batch once. The limits SHALL be read off the
event loop's clock plus the time `advance_time` moved. Without `rate_limits` nothing SHALL be
limited.

#### Scenario: Two messages in one second

- **WHEN** limits are on and the bot sends two messages into a chat at the same moment
- **THEN** the second raises `TelegramRetryAfter` with `retry_after` 1, and is not stored

#### Scenario: Waiting out the refusal

- **WHEN** the test advances the time by that `retry_after`
- **THEN** the next send into the chat goes through

#### Scenario: A busy forum

- **WHEN** the bot sends 20 messages within a minute into two topics of one group
- **THEN** the 21st raises `TelegramRetryAfter`

## REMOVED Requirements

### Requirement: Permissions are stored but not enforced

**Reason**: The bot's own calls are now checked against its rights; see "The bot's own
calls are checked against its rights". User actors are still not checked.

**Migration**: Declare the bot's standing with `bot_status=` or
`Blueprint.set_member(chat, blueprint.bot, rights=...)`, or build the environment with
`enforce_bot_rights=False` while migrating.
