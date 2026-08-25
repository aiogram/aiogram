## ADDED Requirements

### Requirement: Forum topics are declared and modeled

A blueprint SHALL be able to declare forum topics on a chat, which marks that chat as a
forum. Each topic SHALL own its own thread of messages, and the environment SHALL track a
topic's name, icon and open/closed state.

#### Scenario: Declaring a topic makes the chat a forum

- **WHEN** a blueprint declares a topic on a supergroup
- **THEN** every environment built from it exposes that topic, and the chat reports itself
  as a forum

#### Scenario: Messages belong to their topic

- **WHEN** messages are sent in two different topics of the same chat
- **THEN** each topic's thread contains only its own messages, while the chat still lists
  all of them

### Requirement: Forum methods drive topic state

The forum management methods SHALL be applied to the world instead of being synthesized:
creating, editing, closing, reopening and deleting a topic, unpinning all of a topic's
messages, and the General-topic variants. Each SHALL emit the matching service message
into the chat where Telegram would.

#### Scenario: Creating a topic

- **WHEN** a handler calls `createForumTopic`
- **THEN** the returned topic exists in the chat with the requested name, and a
  `forum_topic_created` service message appears in the chat

#### Scenario: Closing and reopening a topic

- **WHEN** a handler closes a topic and later reopens it
- **THEN** the topic's state follows, and `forum_topic_closed` and `forum_topic_reopened`
  service messages are appended in order

#### Scenario: Editing a topic

- **WHEN** a handler edits a topic's name or icon
- **THEN** the stored topic reflects the change and a `forum_topic_edited` service message
  is emitted

#### Scenario: Deleting a topic

- **WHEN** a handler deletes a topic
- **THEN** the topic and its messages are gone from the chat, and a later attempt to post
  into it fails with the error Telegram would return

### Requirement: Actors can be bound to a topic

A user actor SHALL be bindable to a topic of a forum chat, and every update it produces
SHALL carry the topic's thread identifier and be marked as a topic message, so that
handler replies stay inside the topic exactly as they do in production.

#### Scenario: Triggering inside a topic

- **WHEN** an actor bound to a topic sends a message
- **THEN** the update carries that topic's `message_thread_id` and `is_topic_message`, and
  a handler replying with `message.answer(...)` produces a message in the same topic

#### Scenario: Topic binding does not leak

- **WHEN** an actor is bound to a topic
- **THEN** the actor it was derived from remains bound to whatever it was bound to before

### Requirement: Business connections are declared and modeled

A blueprint SHALL be able to declare business connections, each carrying the owning user,
the connection's chat identifier, whether it is enabled, and the bot's rights. The
environment SHALL answer `getBusinessConnection` from that state, and SHALL apply
`readBusinessMessage` and `deleteBusinessMessages` to the world.

#### Scenario: Reading a declared connection

- **WHEN** a handler calls `getBusinessConnection` for a declared connection
- **THEN** it receives the declared owner, rights and enabled flag

#### Scenario: Deleting business messages

- **WHEN** a handler deletes messages on a business connection
- **THEN** those messages are removed from the chat they belonged to

#### Scenario: Unknown connection

- **WHEN** a handler asks for a connection that was never declared
- **THEN** the call fails with the framework's own error type rather than a synthesized
  connection

### Requirement: Business messages are attributed to the business account

A message sent with a business connection identifier SHALL be stored as sent by the
**business account user**, not by the bot, with the bot recorded as the sending business
bot and the connection identifier carried on the message.

#### Scenario: Sender is the business account

- **WHEN** a handler replies on a business connection
- **THEN** the stored message's sender is the connection's owner, its sending business bot
  is the bot, and its business connection identifier matches the connection

#### Scenario: Ordinary messages are unaffected

- **WHEN** a handler sends a message without a business connection identifier
- **THEN** the stored message is sent by the bot, with no business attribution

### Requirement: Business update triggers

Actors SHALL be able to trigger the business update types: a message on a connection, an
edit of one, a connection being enabled or disabled, and messages being deleted by the
business account.

#### Scenario: Business message reaches its handler

- **WHEN** an actor sends a message on a business connection
- **THEN** the `business_message` handler runs, and the event carries the connection
  identifier

#### Scenario: Connection is disabled

- **WHEN** a connection is disabled through the environment
- **THEN** a `business_connection` update is dispatched whose connection reports itself as
  not enabled, and the declared state follows

#### Scenario: Business messages deleted

- **WHEN** the business account deletes messages
- **THEN** a `deleted_business_messages` update is dispatched listing those message
  identifiers, and the messages are gone from the chat

### Requirement: Communities are declared and triggered

A blueprint SHALL be able to declare a community and attach chats to it. The community
SHALL be visible on the chat's full info, and actors SHALL be able to trigger the
community service messages for a chat being added to, or removed from, a community.

#### Scenario: Community is visible on chat info

- **WHEN** a handler fetches full info for a chat attached to a community
- **THEN** the returned chat carries that community

#### Scenario: Chat added to a community

- **WHEN** the corresponding service message is triggered
- **THEN** the handler receives a message carrying the community, and the message is stored
  in the chat

#### Scenario: Chat removed from a community

- **WHEN** the removal service message is triggered
- **THEN** the handler receives it and the chat is no longer attached to the community

## MODIFIED Requirements

### Requirement: FSM state is inspectable and settable

The environment SHALL expose the FSM context for any user/chat pair so that a test can
assert the resulting state and data after a flow, and can arrange a starting state
without replaying the whole conversation. Resolution SHALL go through the dispatcher's
configured `FSMStrategy` and SHALL accept the topic and the business connection, so that
the key the environment returns is the same key the dispatcher used for the corresponding
event under every strategy.

#### Scenario: Asserting state after a flow

- **WHEN** a flow drives a user into a specific `State`
- **THEN** the test can read that user's current state and data from the environment

#### Scenario: Arranging a starting state

- **WHEN** a test sets a user's state and data before triggering an event
- **THEN** handlers and scenes observe that state, without the earlier steps being replayed

#### Scenario: Topic-scoped strategies resolve the same key as the dispatcher

- **WHEN** the dispatcher uses a topic-aware `FSMStrategy` and a handler stores data for an
  event triggered inside a topic
- **THEN** asking the environment for that user's state in that topic returns the stored
  data, rather than an empty context for a different key

#### Scenario: Business connections are part of the key

- **WHEN** a handler stores data while processing an event on a business connection
- **THEN** asking the environment for that user's state on the same connection returns the
  stored data
