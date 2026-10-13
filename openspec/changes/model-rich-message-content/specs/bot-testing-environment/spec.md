## ADDED Requirements

### Requirement: A rich message carries the content its request stated

A rich message the environment stores, whether sent, edited, copied or forwarded, SHALL
carry the blocks and settings its request stated, in the shape Telegram returns them. Media
inside a block SHALL be synthesized as it is for the matching send method. A field the
stored shape requires but the request left unset SHALL get a valid value. Content given
only as `html` or `markdown` is not parsed into blocks.

#### Scenario: Sent blocks are stored

- **WHEN** a handler sends a rich message whose blocks include a paragraph, a list, a table
  and a button block
- **THEN** the stored message's rich content has the same blocks in the same order,
  carrying the same text, cells and buttons

#### Scenario: Media inside a block is synthesized

- **WHEN** a handler sends a rich message containing a photo block marked as a spoiler
- **THEN** the stored block carries a non-empty, schema-valid photo, the same as a photo
  sent with `sendPhoto`, and is marked as a spoiler

#### Scenario: Unset required fields get valid values

- **WHEN** a handler sends a map block without zoom or size, or a list without item labels
- **THEN** the stored blocks carry values within the ranges the Bot API documents for them

#### Scenario: Markup-only content is not parsed

- **WHEN** a handler sends a rich message given only as `html` or `markdown`
- **THEN** the message is stored and returned, and its rich content carries no blocks

#### Scenario: A copied rich message keeps its content

- **WHEN** a handler copies or forwards a stored rich message
- **THEN** the resulting message carries the same rich content

### Requirement: Editing text replaces either kind of content

`editMessageText` SHALL replace a stored message's content with what the request carries:
rich content replaces text and text replaces rich content, so the message never carries
both. The reply markup SHALL follow the method's existing rule: what the request passes,
and none when it passes none.

#### Scenario: Editing in rich content

- **WHEN** a handler edits a stored text message with rich content
- **THEN** the stored message carries the new blocks and no longer carries the old text

#### Scenario: Editing a rich message back to text

- **WHEN** a handler edits a stored rich message with plain text
- **THEN** the stored message carries the text and no longer carries rich content

#### Scenario: Editing only the keyboard keeps the rich content

- **WHEN** a handler edits the reply markup of a stored rich message
- **THEN** the rich content is unchanged and the new keyboard is stored

### Requirement: Buttons inside rich content are clickable

A click trigger SHALL resolve a `callback_data` from a button anywhere in a stored rich
message's content, at any nesting depth, as well as from its inline keyboard, and SHALL
accept such a button object directly. Buttons SHALL be considered in document order: the
inline keyboard first, then the blocks. Deep-link following and the misdirected-click hint
SHALL cover these buttons the same way.

#### Scenario: Clicking a button block

- **WHEN** a handler sends a rich message with a callback button in a button block, and a
  user actor clicks its `callback_data`
- **THEN** a `callback_query` update is dispatched whose `data` is that `callback_data` and
  whose `message` is the stored rich message

#### Scenario: Clicking a button nested in text

- **WHEN** the callback button sits in rich text inside a nested block, such as a list item
  or a details block
- **THEN** the click resolves it exactly as it resolves a top-level button block

#### Scenario: Clicking a rich button object

- **WHEN** a test passes a button object taken from stored rich content to the click
  trigger
- **THEN** the click uses that button's `callback_data`

#### Scenario: Following a deep link from a rich button

- **WHEN** a handler sends a rich message whose `url` button carries a start link to the
  bot, and a user actor follows the deep link
- **THEN** the link is followed exactly as it is from an inline keyboard button

#### Scenario: A rich button in another chat is named

- **WHEN** an actor clicks a `callback_data` that exists only on a rich button in a
  different chat
- **THEN** the failure names that chat, as it does for an inline keyboard button
