## ADDED Requirements

### Requirement: A rich message carries the content its request stated

A rich message the environment stores, whether sent or edited, SHALL carry the blocks its
request stated, in the shape Telegram returns them. Media inside a block and required
fields the request does not state SHALL be synthesized. Content given only as `html` or
`markdown` is not parsed into blocks.

#### Scenario: Sent blocks are stored

- **WHEN** a handler sends a rich message whose blocks include a paragraph, a list and a
  button block
- **THEN** the stored message's rich content has the same blocks in the same order,
  carrying the same text and buttons

#### Scenario: Media inside a block is synthesized

- **WHEN** a handler sends a rich message containing a photo block
- **THEN** the stored block carries a schema-valid photo, the same as a photo sent with
  `sendPhoto`

#### Scenario: Editing replaces the rich content

- **WHEN** a handler edits a stored rich message with new rich content
- **THEN** the stored message carries the new blocks, and no other field of the message is
  cleared by the edit

#### Scenario: Markup-only content is not parsed

- **WHEN** a handler sends a rich message given only as `html` or `markdown`
- **THEN** the message is stored and returned, and its rich content carries no blocks

### Requirement: Buttons inside rich content are clickable

A click trigger SHALL resolve a `callback_data` from a button anywhere in a stored rich
message's content, at any nesting depth, as well as from its inline keyboard. A
misdirected click SHALL name the chat holding such a button the same way it does for an
inline keyboard button.

#### Scenario: Clicking a button block

- **WHEN** a handler sends a rich message with a callback button in a button block, and a
  user actor clicks its `callback_data`
- **THEN** a `callback_query` update is dispatched whose `data` is that `callback_data` and
  whose `message` is the stored rich message

#### Scenario: Clicking a button nested in text

- **WHEN** the callback button sits in rich text inside a nested block, such as a list item
  or a details block
- **THEN** the click resolves it exactly as it resolves a top-level button block

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
