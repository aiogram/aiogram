## MODIFIED Requirements

### Requirement: Supported event triggers

The toolkit SHALL provide a trigger for **every** `Update` variant the framework defines,
so no registered handler is unreachable from a test. This includes the conversational
kinds already supported — sending and editing messages, sending media and captions,
pressing an inline keyboard button, answering an inline query, and chat member
transitions — and additionally channel posts and their edits, chosen inline results,
shipping and pre-checkout queries, purchased paid media, chat join requests, chat boosts
and their removal, guest messages, managed bot updates and subscription updates. Each
trigger SHALL produce an update indistinguishable in shape from one Telegram would
deliver.

Poll, poll answer and message reaction triggers are specified alongside the state they
read.

#### Scenario: Pressing an inline keyboard button

- **WHEN** a user actor clicks a button of a message previously sent by the bot
- **THEN** a `callback_query` update is dispatched whose `data` and `message` come from
  the real button and the real stored message

#### Scenario: Chat member transition

- **WHEN** a user actor joins a group chat
- **THEN** a `chat_member` update with correct `old_chat_member` / `new_chat_member`
  statuses is dispatched, and the environment's membership state reflects the new status

#### Scenario: Editing a message sent by a user

- **WHEN** a user actor edits a message it previously sent
- **THEN** an `edited_message` update is dispatched and the stored message content changes

#### Scenario: Every update kind is reachable

- **WHEN** the framework defines an `Update` variant
- **THEN** the toolkit exposes a trigger producing it, and a test asserting this over the
  full set of variants passes without exception

#### Scenario: Posting to a channel

- **WHEN** a post is made to a chat declared as a channel
- **THEN** a `channel_post` update is dispatched rather than a `message` update, and the
  post is stored in that chat

## ADDED Requirements

### Requirement: Outstanding queries are tracked and answers validated

Every trigger that produces a query — callback query, inline query, shipping query,
pre-checkout query — SHALL register that query's identifier as outstanding. The
corresponding answer methods SHALL be applied to that registry: answering an outstanding
query SHALL succeed and clear it, and answering an unknown or already-answered identifier
SHALL raise `TelegramBadRequest`, as Telegram does when a query has expired or was already
answered.

#### Scenario: Answering an outstanding callback query succeeds

- **WHEN** a handler answers the callback query it is currently processing
- **THEN** the call succeeds and the query is no longer outstanding

#### Scenario: Answering twice fails

- **WHEN** a handler answers the same callback query a second time
- **THEN** the second call raises `TelegramBadRequest`

#### Scenario: Answering a fabricated identifier fails

- **WHEN** a handler answers a callback query identifier the environment never issued
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: The rule covers every query kind

- **WHEN** an inline query, a shipping query or a pre-checkout query is answered with an
  identifier that is not outstanding
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Chat join requests are world state

A blueprint SHALL be able to declare pending join requests, and a trigger SHALL produce a
`chat_join_request` update while recording the request. `approveChatJoinRequest` SHALL make
the requester a member of the chat and clear the request; `declineChatJoinRequest` SHALL
clear the request without adding the member. Both SHALL raise `TelegramBadRequest` when no
such request is pending.

#### Scenario: Approving a request adds the member

- **WHEN** a user actor requests to join a chat and a handler approves it
- **THEN** the request is no longer pending and the user is a member of that chat

#### Scenario: Declining a request leaves the user out

- **WHEN** a handler declines a pending request
- **THEN** the request is no longer pending and the user is not a member

#### Scenario: Acting on a request that does not exist fails

- **WHEN** a handler approves a join request for a user who never requested to join
- **THEN** the call raises `TelegramBadRequest`

### Requirement: A payment flow can be driven end to end

The environment SHALL support exercising a full payment interaction: a shipping query, a
pre-checkout query, and the resulting message carrying `successful_payment`. Each step
SHALL be an actor trigger, and the bot's answers SHALL be validated against the query
registry.

#### Scenario: Completing a payment

- **WHEN** a test triggers a shipping query, the handler answers it, a pre-checkout query
  follows, the handler answers that, and the payment is triggered
- **THEN** a message carrying `successful_payment` is appended to the chat and reaches the
  handler registered for it

#### Scenario: Failing a pre-checkout

- **WHEN** a handler answers a pre-checkout query with `ok=False` and an error message
- **THEN** the call succeeds, the query is cleared, and no `successful_payment` message is
  produced unless the test triggers one

### Requirement: Channel chats are declarable

A blueprint SHALL be able to declare a channel chat, and messages posted to it SHALL route
as channel posts. Editing a stored channel post SHALL produce an `edited_channel_post`
update.

#### Scenario: Declaring a channel

- **WHEN** a blueprint declares a channel and a post is triggered in it
- **THEN** the handler registered for `channel_post` receives it, and the handler
  registered for `message` does not
