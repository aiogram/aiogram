## MODIFIED Requirements

### Requirement: Modeled Bot API methods mutate world state

Bot API calls made by handlers SHALL be intercepted. For methods the environment models,
the call SHALL be applied to the world state and SHALL return a result consistent with
that state. Modeled methods SHALL cover at minimum: sending messages and media, sending
invoices, games, paid media, checklists and rich messages, editing message text, caption,
reply markup, media, live location and checklist, deleting messages, forwarding and
copying messages singly and in batches, pinning, unpinning and unpinning all, answering
callback queries, and chat member administration.

#### Scenario: Sending a message appends it to the chat

- **WHEN** a handler calls `message.answer("Welcome!")`
- **THEN** a new `Message` appears in that chat's message list with the bot as sender, a
  unique `message_id`, and the resolved text

#### Scenario: Editing mutates the stored message

- **WHEN** a handler edits the text of a message the bot sent earlier
- **THEN** the stored message's text changes in place, and no additional message is added
  to the chat

#### Scenario: Deleting removes the message

- **WHEN** a handler deletes a message
- **THEN** the message is no longer present in the chat's message list, and a later
  attempt to edit it fails with the same error Telegram would return

#### Scenario: Bot-level defaults are applied before state is recorded

- **WHEN** the environment's bot declares `parse_mode="HTML"` and a handler sends a
  message without an explicit `parse_mode`
- **THEN** the recorded call and the stored message carry the resolved default

#### Scenario: Every message-producing method stores its message

- **WHEN** a handler calls `sendInvoice`, `sendGame`, `sendPaidMedia`, `sendChecklist`,
  `sendLivePhoto` or `sendRichMessage`
- **THEN** a `Message` carrying the corresponding payload field appears in the chat with a
  unique `message_id`, and the returned object is that stored message

#### Scenario: A button on any sent message is clickable

- **WHEN** a handler sends an invoice or a rich message carrying an inline keyboard, and a
  user actor clicks one of its buttons
- **THEN** the button is resolved from the stored message, exactly as it is for a message
  sent with `sendMessage`

## ADDED Requirements

### Requirement: The whole edit surface mutates stored messages

Editing a stored message's media, live location or checklist SHALL mutate that message in
place rather than returning a synthesized result, and stopping a live location SHALL
return the stored message. Each SHALL fail with `TelegramBadRequest` when the target
message is unknown or deleted, and when the target is an inline message, matching the
behavior of the already-modeled text and caption edits.

#### Scenario: Editing media replaces the stored media

- **WHEN** a handler calls `editMessageMedia` on a photo message it sent earlier
- **THEN** the stored message carries the new media in the field matching the input media
  type, its caption reflects the new input, and no additional message is added to the chat

#### Scenario: Editing a live location moves the stored message

- **WHEN** a handler calls `editMessageLiveLocation` on a message it sent with
  `sendLivePhoto` or `sendLocation`
- **THEN** the stored message's `location` reports the new coordinates

#### Scenario: Stopping a live location returns the stored message

- **WHEN** a handler calls `stopMessageLiveLocation` for a stored message
- **THEN** the returned `Message` is that stored message, not a synthesized one

#### Scenario: Editing an unknown message fails like Telegram

- **WHEN** a handler edits the media of a message that was deleted
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Editing an inline message says it is unmodeled

- **WHEN** a handler edits the media of a message addressed by `inline_message_id`
- **THEN** the call raises `TelegramBadRequest` naming inline messages as unmodeled,
  rather than silently succeeding

### Requirement: A sent message carries the values its request stated

A message the environment stores SHALL carry the scalar values its request actually
carried, rather than synthesized substitutes, wherever the request states them. Media
content itself remains synthesized.

#### Scenario: A sent location keeps its coordinates

- **WHEN** a handler calls `sendLocation` with a latitude, longitude and live period
- **THEN** the stored message's `location` reports those values, not synthesized ones

#### Scenario: A request field is not forced into an incompatible payload field

- **WHEN** a request field shares a name with a payload field of a different type, such as
  a `sendVideo` cover file id against a `Video.cover` photo
- **THEN** the payload field keeps its synthesized value rather than the raw request value

### Requirement: Batch forward and copy produce real messages

Forwarding or copying several messages at once SHALL apply the same world semantics as the
single-message forms, appending one message per source to the target chat and returning
identifiers that exist in that chat.

#### Scenario: Forwarding a batch

- **WHEN** a handler calls `forwardMessages` with three message ids from another chat
- **THEN** three messages appear in the target chat carrying forward origin information,
  and the returned identifiers match their stored `message_id` values

#### Scenario: Copying a batch omits the source attribution

- **WHEN** a handler calls `copyMessages`
- **THEN** the copies appear in the target chat without forward origin information

#### Scenario: A batch from an unknown chat fails

- **WHEN** a handler forwards messages from a chat the environment does not know
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Unpinning all messages clears the pinned list

`unpinAllChatMessages` SHALL clear the chat's pinned message list that `pinChatMessage`
and `unpinChatMessage` maintain.

#### Scenario: Clearing every pin

- **WHEN** a handler pins two messages and then calls `unpinAllChatMessages`
- **THEN** the chat reports no pinned messages

### Requirement: Seeded results are drawn from the world

For methods with no state to mutate but an identifiable answer, the environment SHALL
answer from the world rather than from generic synthesis: `sendChatAction` SHALL verify
the chat exists, `getFile` SHALL echo the requested `file_id`, `createInvoiceLink` SHALL
return a deterministic link, and `getUserPersonalChatMessages` SHALL read from that user's
private chat when the environment knows one.

#### Scenario: A chat action against an unknown chat fails

- **WHEN** a handler calls `sendChatAction` for a chat that does not exist
- **THEN** the call raises `TelegramBadRequest`, and a call against a known chat returns
  `True` and is recorded

#### Scenario: getFile echoes the requested file

- **WHEN** a handler calls `getFile` with a `file_id` it obtained from a stored message
- **THEN** the returned `File` carries that same `file_id`
