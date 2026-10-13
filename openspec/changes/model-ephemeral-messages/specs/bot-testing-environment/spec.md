## ADDED Requirements

### Requirement: Ephemeral messages are addressed to one receiver

A message the bot sends with ephemeral message parameters SHALL be returned in Telegram's
ephemeral shape: message id 0, an ephemeral message id, and the receiver. It SHALL be kept
apart from the chat's shared history, readable back per receiver in send order, and SHALL
keep its topic thread. It SHALL be refused outside a group or supergroup, and for a
receiver the world does not declare.

#### Scenario: An ephemeral send has Telegram's shape

- **WHEN** a handler sends a message to a group with ephemeral message parameters naming a
  user
- **THEN** the returned message has `message_id` 0, an `ephemeral_message_id`, and that
  user as `receiver_user`

#### Scenario: An ephemeral message stays out of the shared history

- **WHEN** a handler sends an ephemeral message to a group
- **THEN** the group's message list does not contain it, and a wait for the next message in
  that group is not satisfied by it

#### Scenario: An ephemeral message is readable back for its receiver

- **WHEN** a test asks the chat for the ephemeral messages sent to a user
- **THEN** it gets the ephemeral messages the bot sent to that user, in the order they were
  sent, and none the user sent

#### Scenario: An ephemeral send outside a group is rejected

- **WHEN** a handler sends an ephemeral message to a private chat or a channel
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: An ephemeral send to an undeclared user is a setup error

- **WHEN** a handler sends an ephemeral message naming a user the world does not declare
- **THEN** the call fails as a setup error naming that user, and nothing is stored

#### Scenario: An ephemeral send keeps its topic

- **WHEN** a handler sends an ephemeral message into a forum topic
- **THEN** the returned message carries that topic's thread identifier

### Requirement: Only the receiver can click an ephemeral message

A click trigger SHALL resolve buttons on the ephemeral messages addressed to the clicking
actor, ahead of the shared history, and on no other ephemeral message, including one passed
explicitly. A miss SHALL name the receiver of the ephemeral message that holds the button.
The produced `callback_query` SHALL carry the ephemeral message.

#### Scenario: The receiver clicks an ephemeral button

- **WHEN** a handler sends an ephemeral message with a callback button to a member, and
  that member's actor clicks it
- **THEN** a `callback_query` update is dispatched whose `message` is the ephemeral message,
  carrying its `ephemeral_message_id` and `receiver_user`

#### Scenario: Another member cannot click it

- **WHEN** a different member of the same chat clicks that `callback_data`, by data or by
  passing the ephemeral message itself
- **THEN** the click fails, and the failure names the member the ephemeral message is
  addressed to rather than reading as a `callback_data` that exists nowhere

#### Scenario: An answer cannot replace an ephemeral message

- **WHEN** a handler answers a callback query from an ephemeral message with an ephemeral
  message that asks to replace the original
- **THEN** the call fails as a Telegram error, because the Bot API requires ephemeral
  messages to be edited with the ephemeral edit methods instead

### Requirement: Ephemeral edits and deletions act on stored ephemeral messages

The ephemeral edit methods SHALL change the stored ephemeral message they name, addressed by
chat, receiver and ephemeral id: text or rich content, caption, media and reply markup. The
ephemeral delete method SHALL remove it. A call naming a message that does not exist for
that chat and receiver SHALL fail as a Telegram error. The regular edit and delete methods
SHALL NOT reach ephemeral messages.

#### Scenario: Editing an ephemeral message's text

- **WHEN** a handler edits the text of an ephemeral message it sent
- **THEN** the stored ephemeral message carries the new text, and the shared history is
  unchanged

#### Scenario: Deleting an ephemeral message

- **WHEN** a handler deletes an ephemeral message it sent
- **THEN** it is no longer readable back for its receiver, and a later edit of it fails

#### Scenario: Editing through the message's own shortcut

- **WHEN** a handler edits or deletes an ephemeral message through that message object's own
  ephemeral shortcuts
- **THEN** the calls address the stored message and succeed

#### Scenario: The wrong receiver does not match

- **WHEN** a handler edits an ephemeral message by its id but names a different receiver
- **THEN** the call fails as a Telegram error, and the stored message is unchanged

#### Scenario: Regular edits do not reach ephemeral messages

- **WHEN** a handler calls the regular text edit or delete shortcut on an ephemeral message
- **THEN** the call fails as a Telegram error, and the stored ephemeral message is unchanged

### Requirement: Actors can send ephemeral commands

The send trigger SHALL be able to produce an incoming ephemeral message, in a group or
supergroup only: message id 0 and an ephemeral message id, kept out of the shared history,
whether the actor produced it or a test fed it directly. A bot message replying to it SHALL
have to be ephemeral and SHALL have to name an incoming ephemeral message that exists in
that chat. Such a reply carries no `reply_to_message`.

#### Scenario: Sending an ephemeral command

- **WHEN** a user actor in a group sends a command marked as ephemeral, twice
- **THEN** each dispatched message has `message_id` 0 and its own `ephemeral_message_id`,
  and the group's message list contains neither

#### Scenario: Replying with the message's own reply shortcut

- **WHEN** a handler answers that command with `message.reply(...)`
- **THEN** the reply is an ephemeral message addressed to the command's sender, with no
  `reply_to_message`

#### Scenario: A non-ephemeral reply to an ephemeral message is rejected

- **WHEN** a handler replies to an ephemeral command by its `ephemeral_message_id` without
  ephemeral message parameters
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: A reply must name an incoming ephemeral message

- **WHEN** a handler replies naming an `ephemeral_message_id` that no user sent in that
  chat, including the id of the bot's own ephemeral message
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: An ephemeral command outside a group is a setup error

- **WHEN** a test sends an ephemeral command from an actor bound to a private chat
- **THEN** the trigger fails as a setup error, and nothing is dispatched
