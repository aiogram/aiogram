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

### Requirement: A user actor can manage the topics of a forum

A user actor SHALL be able to create a topic, close, reopen and delete one, hide and unhide
the General topic, and close and reopen it. Each SHALL change the world as the matching bot
method does, by the same code, and SHALL store and feed the service message Telegram posts
for it, from that user: `forum_topic_created`, `forum_topic_closed`, `forum_topic_reopened`,
`general_forum_topic_hidden` or `general_forum_topic_unhidden`. Deleting a topic, and closing
or reopening the General topic, SHALL feed nothing, as no service message is modeled for them.
A topic SHALL be named as a declaration, a state or a thread id, and default to the topic the
actor is bound to. The actor SHALL be the owner or an administrator holding
`can_manage_topics` in a chat that is a forum, whatever `enforce_bot_rights` says; otherwise
the trigger SHALL raise `WorldLookupError` naming the right and how to grant it, and change
nothing.

#### Scenario: The owner closes a topic

- **WHEN** the owner of a forum closes one of its topics
- **THEN** the topic is closed and a `forum_topic_closed` message from the owner, in the
  topic and replying to its root, is stored and handled by the dispatcher

#### Scenario: Deleting a topic

- **WHEN** an administrator with `can_manage_topics` deletes a topic
- **THEN** the topic and its messages are gone, nothing is fed, and a later bot call into the
  thread fails with `TOPIC_DELETED`

#### Scenario: A member without the right

- **WHEN** a plain member creates a topic
- **THEN** `WorldLookupError` names `can_manage_topics` and how to grant it, and no topic or
  message is added

## MODIFIED Requirements

### Requirement: The bot's own calls are checked against its rights

Unless the environment is built with `enforce_bot_rights=False`, a call the bot makes into a
group, a supergroup or a channel SHALL fail with Telegram's wording when the bot's standing
there does not allow it. The rules SHALL be one table from method type to the right it takes,
consulted once per call, for recorded-only methods too. Pinning and unpinning SHALL take
`can_pin_messages`, or `can_edit_messages` in a channel. Banning, unbanning and restricting
members and sender chats, and changing the chat's permissions, SHALL take
`can_restrict_members`, and promoting `can_promote_members`; unbanning and promoting in a basic
group SHALL fail with `method is available only in supergroup and channel chats` before any
right is read. Touching the owner SHALL fail with `can't remove chat owner` before the rights in
a supergroup or a channel. Changing the chat's title, description, photo or sticker set SHALL
take `can_change_info`, setting a member's tag `can_manage_tags`, approving and declining
suggested posts `can_post_messages`, and managing invite links and join requests
`can_invite_users`. A topic method SHALL check the rights before it looks the topic up. Creating
a topic SHALL take `can_manage_topics`, and so SHALL editing, closing and reopening a topic the
bot did not create and every General topic method but unpinning; deleting a topic the bot did
not create SHALL take `can_delete_messages`. Deleting someone else's message SHALL take
administrator status in a basic group and `can_delete_messages` elsewhere. A send, copy or
forward by a bot that is not an administrator SHALL take the chat's permission for that kind of
message, narrowed by the bot's own restriction; a live location SHALL be refused as one, and
paid media SHALL be checked only when forwarded or copied, taking both `can_send_photos` and
`can_send_videos`. Posting into a channel SHALL take `can_post_messages`. The owner SHALL hold
every right, and the chat's permissions SHALL NOT grant the bot an administrator's right. A bot
that was removed from the chat or left it SHALL be refused every such call and every send with
`TelegramForbiddenError` and the Bot API server's text. Private chats and user actors SHALL NOT
be checked. With `enforce_bot_rights=False`, the bot SHALL hold every right.

#### Scenario: A member bot pins

- **WHEN** the bot, a plain member of a supergroup, pins a message
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to manage pinned messages in the chat`

#### Scenario: A member bot bans

- **WHEN** the bot, a plain member of a supergroup, bans a user
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to restrict/unrestrict chat member`, and the user stays

#### Scenario: A member bot renames the chat

- **WHEN** the bot, a plain member of a group, sets the chat's title
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to change chat title`

#### Scenario: A member bot changes the chat's permissions

- **WHEN** the bot, a plain member of a supergroup, sets the chat's permissions
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to change chat permissions`, and the permissions stay

#### Scenario: Promoting in a basic group

- **WHEN** the bot, an administrator of a basic group, promotes a member
- **THEN** the call raises `TelegramBadRequest` with
  `method is available only in supergroup and channel chats`

#### Scenario: The bot closes its own topic

- **WHEN** the bot, a plain member of a forum, closes a topic it created
- **THEN** the topic closes, while closing a topic someone else created raises
  `TelegramBadRequest` with `not enough rights to close or open the topic`

#### Scenario: A member bot sends into a silenced chat

- **WHEN** the chat's permissions forbid text and the bot, a plain member, sends text
- **THEN** the call raises `TelegramBadRequest` with
  `not enough rights to send text messages to the chat`, while a user actor's message in
  the same chat is still delivered

#### Scenario: A kicked bot sends

- **WHEN** the bot's status in a supergroup is kicked and it sends a message there
- **THEN** the call raises `TelegramForbiddenError` with
  `Forbidden: bot was kicked from the supergroup chat`, and nothing is stored

#### Scenario: Opting out

- **WHEN** the environment is built with `enforce_bot_rights=False`
- **THEN** the same bot pins, bans and sends as if it held every right

### Requirement: A closed topic refuses those who cannot manage topics

A message the bot sends, copies or forwards into a closed topic, or into the General topic
while it is closed or hidden, SHALL fail with `TOPIC_CLOSED` unless the bot is the chat's
owner, an administrator holding `can_manage_topics`, or the topic's creator. A refused
message SHALL use no message id. User actors SHALL NOT be refused.

#### Scenario: A member bot posts into a closed topic

- **WHEN** the bot, a plain member, sends a message into a closed topic someone else
  created
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_CLOSED`

#### Scenario: An administrator managing topics posts into it

- **WHEN** the bot holds `can_manage_topics` and sends into a closed topic
- **THEN** the message is stored in that topic

#### Scenario: The bot posts into its own closed topic

- **WHEN** the bot, a plain member, sends into a closed topic it created
- **THEN** the message is stored in that topic

#### Scenario: A hidden General topic

- **WHEN** the bot, a plain member, sends a message into a forum whose General topic is
  hidden
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_CLOSED`

### Requirement: A user actor can manage the topics of a forum

A user actor SHALL be able to create a topic, close, reopen and delete one, hide and unhide
the General topic, and close and reopen it. Each SHALL change the world as the matching bot
method does, by the same code, and SHALL store and feed the service message Telegram posts
for it, from that user: `forum_topic_created`, `forum_topic_closed`, `forum_topic_reopened`,
`general_forum_topic_hidden` or `general_forum_topic_unhidden`, and `forum_topic_closed` or
`forum_topic_reopened` for the General topic. Deleting a topic SHALL feed nothing, as
Telegram posts no message for it. A topic deleted since an actor was bound to it SHALL be a
setup error, never a Telegram error.
A topic SHALL be named as a declaration, a state or a thread id, and default to the topic the
actor is bound to. The actor SHALL hold `can_manage_topics` in a chat that is a forum,
whatever `enforce_bot_rights` says: as the owner or an administrator granted it, or, to
create a topic, as the chat's permission of that name, which SHALL bind administrators as
much as members and SHALL be narrowed by the actor's own restriction. The creator of a topic
SHALL close, reopen and delete it without the right. Otherwise the trigger SHALL raise
`WorldLookupError` naming the right and how to grant it, and change nothing.

#### Scenario: The owner closes a topic

- **WHEN** the owner of a forum closes one of its topics
- **THEN** the topic is closed and a `forum_topic_closed` message from the owner, in the
  topic and replying to its root, is stored and handled by the dispatcher

#### Scenario: Deleting a topic

- **WHEN** an administrator with `can_manage_topics` deletes a topic
- **THEN** the topic and its messages are gone, nothing is fed, and a later bot call into the
  thread fails with `message thread not found`

#### Scenario: A member the chat lets create topics

- **WHEN** the chat's permissions grant `can_manage_topics` and a plain member creates a topic
- **THEN** the topic exists with that member as its creator, who may then close, reopen and
  delete it

#### Scenario: A member without the right

- **WHEN** a plain member creates a topic in a chat whose permissions deny `can_manage_topics`
- **THEN** `WorldLookupError` names `can_manage_topics` and how to grant it, and no topic or
  message is added

### Requirement: Flood limits can be modeled per chat

An environment built with `rate_limits` SHALL refuse a message-producing call into a chat
that is over a limit with error 429, `Too Many Requests: retry after N`, and a
`TelegramRetryAfter` whose `retry_after` is the whole seconds until a send into that chat is
allowed. The default limits SHALL be one message per second in any chat and 20 per minute
in a group or supergroup, counted for the whole chat across its topics. The limits SHALL be
read only after the checks Telegram makes before sending, so a call refused for the bot's
rights, its thread or the message it replies to SHALL fail with that refusal, and a refused
call SHALL change nothing. The counted methods SHALL be the modeled sends, read off the
modeling registry. A call SHALL be counted once it succeeds, a media group or batch once.
The limits SHALL be read off the event loop's clock plus the time `advance_time` moved.
Without `rate_limits` nothing SHALL be limited.

#### Scenario: Two messages in one second

- **WHEN** limits are on and the bot sends two messages into a chat at the same moment
- **THEN** the second raises `TelegramRetryAfter` with `retry_after` 1, and is not stored

#### Scenario: A refusal Telegram makes first

- **WHEN** the chat is over its limit and the bot sends into a thread it does not have
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Waiting out the refusal

- **WHEN** the test advances the time by that `retry_after`
- **THEN** the next send into the chat goes through

#### Scenario: A busy forum

- **WHEN** the bot sends 20 messages within a minute into two topics of one group
- **THEN** the 21st raises `TelegramRetryAfter`

### Requirement: Topic refusals use Telegram's wording

A send, copy or forward the bot makes into a thread the chat does not have SHALL fail with
`message thread not found`, whether the chat never had it or `deleteForumTopic` removed it,
as the Bot API server looks the topic up first. So SHALL one into thread 1 of a forum
supergroup, the General topic's id. A forum method naming a topic `deleteForumTopic` removed
SHALL fail with `TOPIC_DELETED`, and one naming a thread the chat never had with
`message thread not found`. Message 1 of a supergroup or a channel SHALL be reserved for
the chat's creation, so no topic SHALL be numbered 1. A topic a test or an actor names that
the chat lacks, or an actor bound to a topic deleted since, SHALL be a setup error that
names the topic, never a Telegram error.

#### Scenario: Posting into an unknown thread

- **WHEN** a handler sends a message with a thread id the forum never had
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Posting into a deleted topic

- **WHEN** a handler deletes a topic and then posts into it
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: Closing a deleted topic

- **WHEN** a handler deletes a topic and then closes it
- **THEN** the call raises `TelegramBadRequest` with `TOPIC_DELETED`

#### Scenario: Posting into thread 1

- **WHEN** a handler sends a message with thread id 1 into a forum
- **THEN** the call raises `TelegramBadRequest` with `message thread not found`

#### Scenario: A test names an unknown topic

- **WHEN** a test binds an actor to a thread id the chat does not have
- **THEN** it raises `WorldLookupError` naming the topics the chat has

#### Scenario: An actor bound to a deleted topic

- **WHEN** an actor bound to a topic sends after the topic was deleted
- **THEN** it raises `WorldLookupError` saying the topic was deleted

### Requirement: A topic message replies to the topic's root

A message stored in a supergroup's forum topic other than General that replies to no
message of its chat SHALL carry the topic's `forum_topic_created` service message as its
`reply_to_message`, and SHALL be marked as a topic message. This SHALL hold for the bot's
sends, copies, forwards and topic service messages and for messages a user actor sends. An
explicit reply SHALL keep its own target, and a reply in another chat SHALL still carry the
root. A replied message SHALL carry no `reply_to_message` of its own, for an actor's reply
as for the bot's. A private chat's topic SHALL give no implicit reply.

#### Scenario: A handler reads the topic name

- **WHEN** an actor bound to a topic sends a message
- **THEN** the handler receives it with `reply_to_message.forum_topic_created` naming the
  topic

#### Scenario: An explicit reply keeps its target

- **WHEN** the bot replies to a message inside a topic
- **THEN** the stored message replies to that message, not to the root

#### Scenario: An actor replies inside a topic

- **WHEN** an actor replies to a message in a topic, which replies to the root itself
- **THEN** the stored reply's `reply_to_message` is that message, carrying no reply of its
  own

#### Scenario: The General topic has no root

- **WHEN** the bot sends a message into the General topic of a forum
- **THEN** the stored message replies to nothing

### Requirement: Forum methods drive topic state

The forum management methods SHALL be applied to the world instead of being synthesized:
creating, editing, closing, reopening and deleting a topic, unpinning all of a topic's
messages, and the General-topic variants. Each SHALL emit the matching service message
into the chat where Telegram would; closing and reopening the General topic SHALL emit
`forum_topic_closed` and `forum_topic_reopened` with no thread id. A private chat SHALL take
creating, editing and deleting a topic and unpinning its messages, and its topic messages
SHALL carry their thread id; closing a topic there, and the General-topic methods, SHALL
fail with `the chat is not a supergroup forum`.

#### Scenario: Creating a topic

- **WHEN** a handler calls `createForumTopic`
- **THEN** the returned topic exists in the chat with the requested name, and a
  `forum_topic_created` service message appears in the chat

#### Scenario: Closing and reopening a topic

- **WHEN** a handler closes a topic and later reopens it
- **THEN** the topic's state follows, and `forum_topic_closed` and `forum_topic_reopened`
  service messages are appended in order

#### Scenario: Closing the General topic

- **WHEN** a handler closes the General topic
- **THEN** it is closed, and a `forum_topic_closed` message with no thread id is appended

#### Scenario: Editing a topic

- **WHEN** a handler edits a topic's name or icon
- **THEN** the stored topic reflects the change and a `forum_topic_edited` service message
  is emitted

#### Scenario: Deleting a topic

- **WHEN** a handler deletes a topic
- **THEN** the topic and its messages are gone from the chat, and a later attempt to post
  into it fails with `message thread not found`, as the Bot API server answers it

#### Scenario: A topic in a private chat

- **WHEN** a handler creates a topic in a private chat and sends into it
- **THEN** the message carries the topic's thread id, is a topic message, and replies to
  nothing

## REMOVED Requirements

### Requirement: Permissions are stored but not enforced

**Reason**: The bot's own calls are now checked against its rights; see "The bot's own
calls are checked against its rights". User actors are still not checked.

**Migration**: Declare the bot's standing with `bot_status=` or
`Blueprint.set_member(chat, blueprint.bot, rights=...)`, or build the environment with
`enforce_bot_rights=False` while migrating.
