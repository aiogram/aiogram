## ADDED Requirements

### Requirement: Ephemeral messages are addressed to one receiver

A message the bot sends with ephemeral message parameters SHALL be returned in Telegram's
ephemeral shape: message id 0, an ephemeral message id, and the receiver. It SHALL be kept
apart from the chat's shared message history, addressable by chat, receiver and ephemeral
id. It SHALL be rejected outside a group or supergroup and for a receiver who is not a
member of the chat.

#### Scenario: An ephemeral send has Telegram's shape

- **WHEN** a handler sends a message to a group with ephemeral message parameters naming a
  member
- **THEN** the returned message has `message_id` 0, an `ephemeral_message_id`, and that
  member as `receiver_user`

#### Scenario: An ephemeral message stays out of the shared history

- **WHEN** a handler sends an ephemeral message to a group
- **THEN** the group's message list does not contain it, and a wait for the next message in
  that group is not satisfied by it

#### Scenario: An ephemeral message is readable back for its receiver

- **WHEN** a test asks the chat for the ephemeral messages addressed to a member
- **THEN** it gets the ephemeral messages sent to that member, in the order they were sent

#### Scenario: An ephemeral send to a non-member is rejected

- **WHEN** a handler sends an ephemeral message naming a user who is not a member of the
  chat
- **THEN** the call fails as a Telegram error, and nothing is stored

#### Scenario: An ephemeral send outside a group is rejected

- **WHEN** a handler sends an ephemeral message to a private chat or a channel
- **THEN** the call fails as a Telegram error, and nothing is stored

### Requirement: Only the receiver can click an ephemeral message

A click trigger SHALL resolve buttons on the ephemeral messages addressed to the clicking
actor, and on no other ephemeral messages. The produced `callback_query` SHALL carry the
ephemeral message.

#### Scenario: The receiver clicks an ephemeral button

- **WHEN** a handler sends an ephemeral message with a callback button to a member, and
  that member's actor clicks it
- **THEN** a `callback_query` update is dispatched whose `message` is the ephemeral message,
  carrying its `ephemeral_message_id` and `receiver_user`

#### Scenario: Another member cannot click it

- **WHEN** a different member of the same chat clicks that `callback_data`
- **THEN** the click fails, and the failure names the member the ephemeral message is
  addressed to rather than reading as a `callback_data` that exists nowhere

### Requirement: Ephemeral edits and deletions act on stored ephemeral messages

The ephemeral edit methods SHALL change the stored ephemeral message they name: text or
rich content, caption, media, and reply markup. The ephemeral delete method SHALL remove
it. A call naming an ephemeral message that does not exist for that chat and receiver SHALL
fail as a Telegram error.

#### Scenario: Editing an ephemeral message's text

- **WHEN** a handler edits the text of an ephemeral message it sent
- **THEN** the stored ephemeral message carries the new text, and the shared history is
  unchanged

#### Scenario: Deleting an ephemeral message

- **WHEN** a handler deletes an ephemeral message it sent
- **THEN** it is no longer readable back for its receiver, and a later edit of it fails

#### Scenario: Editing through the message's own shortcut

- **WHEN** a handler edits an ephemeral message through that message object's own ephemeral
  edit shortcut
- **THEN** the call addresses the stored message and succeeds

### Requirement: Actors can send ephemeral commands

The send trigger SHALL be able to produce an incoming ephemeral message: `message_id` 0
and an `ephemeral_message_id`, kept out of the shared history. A bot message that replies
to it SHALL have to be ephemeral and SHALL have to name an ephemeral message that exists
in that chat. Otherwise the call fails as a Telegram error.

#### Scenario: Sending an ephemeral command

- **WHEN** a user actor in a group sends a command marked as ephemeral
- **THEN** the dispatched message has `message_id` 0 and an `ephemeral_message_id`, and the
  group's message list does not contain it

#### Scenario: Replying with the message's own reply shortcut

- **WHEN** a handler answers that command with `message.reply(...)`
- **THEN** the reply is an ephemeral message addressed to the command's sender

#### Scenario: A non-ephemeral reply to an ephemeral message is rejected

- **WHEN** a handler replies to an ephemeral message by its `ephemeral_message_id` without
  ephemeral message parameters
- **THEN** the call fails as a Telegram error, and nothing is stored
