## MODIFIED Requirements

### Requirement: Supported event triggers

The toolkit SHALL provide a trigger for **every** `Update` variant the framework defines,
with no exemptions, so no registered handler is unreachable from a test. This includes the
conversational kinds — sending and editing messages, sending media and captions, pressing
an inline keyboard button, answering an inline query, and chat member transitions —
channel posts and their edits, chosen inline results, shipping and pre-checkout queries,
purchased paid media, chat join requests, chat boosts and their removal, guest messages,
managed bot updates, subscription updates, and additionally poll updates, poll answers,
message reactions and message reaction counts. Each trigger SHALL produce an update
indistinguishable in shape from one Telegram would deliver.

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
  full set of variants passes with no exemptions declared

#### Scenario: Posting to a channel

- **WHEN** a post is made to a chat declared as a channel
- **THEN** a `channel_post` update is dispatched rather than a `message` update, and the
  post is stored in that chat

## ADDED Requirements

### Requirement: Polls are world state

A poll sent by the bot SHALL be stored on the message that carries it, holding its
question, options, type, anonymity, multiple-answer flag, quiz answer and explanation,
the votes cast, and whether it is closed. A blueprint SHALL be able to declare an existing
poll.

#### Scenario: A sent poll is stored on its message

- **WHEN** a handler calls `sendPoll`
- **THEN** a message carrying that poll is appended to the chat, and the returned message
  is the stored one

#### Scenario: A declared poll is answerable

- **WHEN** a blueprint declares a poll in a chat and a user actor votes in it
- **THEN** the vote is recorded without the poll having been sent through the API first

### Requirement: Voting updates the stored poll

Voting SHALL be an actor trigger that produces a `poll_answer` update and records the
vote against the stored poll, updating its counts. Retracting a vote SHALL be supported
where Telegram supports it. An anonymous poll SHALL additionally be triggerable as a
`poll` update carrying aggregate state.

#### Scenario: A vote reaches the handler and the poll

- **WHEN** a user actor votes for the second option of a stored poll
- **THEN** a `poll_answer` update reaches the registered handler, and the stored poll
  reports one vote for that option

#### Scenario: Vote counts stay consistent with voters

- **WHEN** three users vote across two options and one of them retracts
- **THEN** each option's reported count equals the number of users recorded as having
  chosen it

#### Scenario: Voting in a closed poll fails

- **WHEN** a user actor votes in a poll that has been stopped
- **THEN** the trigger raises an error rather than recording the vote

### Requirement: Stopping a poll closes the stored poll

`stopPoll` SHALL close the poll stored on the target message and return it with its final
vote counts. Stopping a message that is unknown, carries no poll, or whose poll is already
closed SHALL raise `TelegramBadRequest`.

#### Scenario: Stopping returns the poll that was sent

- **WHEN** a handler sends a poll, users vote, and the handler stops it
- **THEN** the returned poll is the stored one, marked closed, carrying the votes cast

#### Scenario: Stopping twice fails

- **WHEN** a handler stops a poll that is already closed
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Stopping a message with no poll fails

- **WHEN** a handler calls `stopPoll` on an ordinary text message
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Reactions are world state

The environment SHALL record the reactions set on a message, per user, and expose them
through the chat rather than through the stored message — the Bot API has no message field
carrying them. `setMessageReaction` (the bot's own reactions on one message),
`deleteMessageReaction` (one actor's reaction off one message) and
`deleteAllMessageReactions` (one actor's reactions across the whole chat) SHALL each be
applied to that state with their own semantics rather than synthesized. The two
message-scoped methods SHALL fail with `TelegramBadRequest` for an unknown or deleted
message.

#### Scenario: The bot reacts to a message

- **WHEN** a handler calls `setMessageReaction` on a stored message
- **THEN** the chat reports that reaction as set by the bot for that message

#### Scenario: Reacting again replaces the previous reaction

- **WHEN** a handler sets a different reaction on a message it already reacted to
- **THEN** the chat reports only the new reaction for the bot

#### Scenario: Counts are aggregated across reactors

- **WHEN** two users and the bot react to the same message
- **THEN** the chat reports a count per distinct reaction matching the number of reactors

#### Scenario: Moderating one reaction off one message

- **WHEN** two users have reacted to a message and a handler calls
  `deleteMessageReaction` naming one of them
- **THEN** only that user's reaction is gone and the other user's remains

#### Scenario: Moderating one actor's reactions across the chat

- **WHEN** a user has reacted to several messages and a handler calls
  `deleteAllMessageReactions` naming that user
- **THEN** none of that user's reactions remain anywhere in the chat, while other users'
  reactions on the same messages are untouched — the method removes an actor's reactions
  chat-wide, not every reaction on one message

### Requirement: Reaction triggers derive from stored state

A user actor SHALL be able to react to a stored message, producing a `message_reaction`
update whose `old_reaction` and `new_reaction` are derived from that message's stored
reactions rather than fabricated, and a `message_reaction_count` update SHALL be
triggerable for the anonymous aggregate form.

#### Scenario: Changing a reaction reports the previous one

- **WHEN** a user actor reacts to a message and then reacts with a different emoji
- **THEN** the second `message_reaction` update reports the first emoji as
  `old_reaction` and the second as `new_reaction`

#### Scenario: Removing a reaction

- **WHEN** a user actor removes its reaction from a message
- **THEN** a `message_reaction` update with an empty `new_reaction` is dispatched and the
  chat no longer reports that user's reaction
