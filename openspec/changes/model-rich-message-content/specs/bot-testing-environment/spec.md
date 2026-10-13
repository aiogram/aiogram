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
