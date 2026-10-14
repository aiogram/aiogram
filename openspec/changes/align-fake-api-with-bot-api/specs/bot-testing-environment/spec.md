## ADDED Requirements

### Requirement: A media group stores its items

`sendMediaGroup` SHALL store one message per item, each carrying that item's media, caption
and caption entities, all under one shared `media_group_id`. A request with fewer than 2 or
more than 10 items SHALL fail as a Telegram error.

#### Scenario: An album keeps each item's media and caption

- **WHEN** a handler sends a media group of two photos with captions
- **THEN** two messages are stored, each with a photo and its own caption, sharing one
  `media_group_id`

#### Scenario: A one-item album is refused

- **WHEN** a handler sends a media group with one item
- **THEN** the call raises `TelegramBadRequest`, and nothing is stored

### Requirement: A reply resolves its target where the request says

A send with reply parameters SHALL look its target up in the chat the parameters name, or in
the target chat otherwise. It SHALL set `reply_to_message` only for a target in the same
chat. A target that does not exist SHALL fail as a Telegram error, unless the request allows
sending without the reply.

#### Scenario: A reply to a missing message fails

- **WHEN** a handler replies to a message id that does not exist in the chat
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Sending without the reply is allowed when asked

- **WHEN** the same reply passes `allow_sending_without_reply`
- **THEN** the message is sent without `reply_to_message`

#### Scenario: A reply in another chat is looked up there

- **WHEN** a handler replies to a message of another chat, naming that chat
- **THEN** the target is resolved in that chat, and the message carries no
  `reply_to_message` from its own chat

### Requirement: Copies and forwards follow the documented rules

A copy or forward SHALL land in the target thread the request names, or in none. A copy
SHALL carry the request's new caption with its entities, drop the caption when asked, and
store the request's inline keyboard. Service, invoice, paid-media and giveaway messages SHALL
not be copied, and protected or service messages SHALL not be forwarded; a single call fails
as a Telegram error and a batch call skips them.

#### Scenario: A copy into a topic lands in it

- **WHEN** a handler copies a message into a forum topic of another chat
- **THEN** the copy carries that topic's thread, and a copy into a non-forum chat carries
  none

#### Scenario: A new caption brings its own entities

- **WHEN** a handler copies a captioned message with a new caption and no entities
- **THEN** the copy carries the new caption and none of the old entities

#### Scenario: A protected message cannot be forwarded

- **WHEN** a handler forwards a message sent with protected content
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: A service message cannot be copied

- **WHEN** a handler copies a service message
- **THEN** the call raises `TelegramBadRequest`, and a batch copy including it skips it

### Requirement: Unpinning without an id unpins the newest pin

`unpinChatMessage` without a message id SHALL unpin only the most recently sent pinned
message, leaving the others pinned.

#### Scenario: Two pins, one unpin

- **WHEN** a handler pins two messages and then unpins without an id
- **THEN** only the more recently sent message is unpinned

### Requirement: An edit acts on the content the message has

`editMessageText` SHALL fail as a Telegram error on a message with no text or rich content,
and `editMessageCaption` SHALL fail on a message with no media that can carry a caption.

#### Scenario: Editing text on a photo fails

- **WHEN** a handler edits the text of a photo message
- **THEN** the call raises `TelegramBadRequest`, and the stored message is unchanged

#### Scenario: Editing a caption on a text message fails

- **WHEN** a handler edits the caption of a text message
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Polls keep their documented settings

A poll SHALL store all of its correct option ids, and SHALL allow revoting by default unless
it is a quiz. A quiz without correct option ids SHALL fail as a Telegram error. `stopPoll`
SHALL store the inline keyboard it is given.

#### Scenario: A quiz keeps its correct answers

- **WHEN** a handler sends a quiz with two correct option ids
- **THEN** the stored poll reports both

#### Scenario: A regular poll allows revoting by default

- **WHEN** a handler sends a regular poll without saying whether revoting is allowed
- **THEN** the stored poll allows revoting

#### Scenario: A quiz without an answer is refused

- **WHEN** a handler sends a quiz with no correct option ids
- **THEN** the call raises `TelegramBadRequest`

### Requirement: Forum topic calls apply their documented couplings

Hiding the General topic SHALL also close it, and reopening it SHALL also unhide it.
`editForumTopic` with an empty name SHALL keep the current name, and an empty custom emoji id
SHALL remove the icon.

#### Scenario: Hiding General closes it

- **WHEN** a handler hides an open General topic
- **THEN** the General topic is hidden and closed

#### Scenario: An empty name keeps the name

- **WHEN** a handler edits a topic with an empty name
- **THEN** the topic keeps its name

### Requirement: Business deletions stay in one chat

`deleteBusinessMessages` SHALL delete messages from one chat only, and SHALL fail as a
Telegram error when the ids belong to different chats.

#### Scenario: Equal ids in another chat are untouched

- **WHEN** two chats of a business connection both hold a message with id 1, and a handler
  deletes id 1 from one of them
- **THEN** the other chat's message stays

### Requirement: Checklists carry their content

A checklist sent or edited SHALL be stored with the title and tasks its request stated.

#### Scenario: A sent checklist keeps its tasks

- **WHEN** a handler sends a checklist with a title and two tasks
- **THEN** the stored checklist carries that title and those two tasks

### Requirement: Synthesized values are valid and distinct

Synthesized content SHALL be schema-valid and distinguishable:

- every synthesized file SHALL get a unique id, and a file id the request passes SHALL be
  the stored one;
- a dice SHALL carry its emoji, 🎲 by default, and a value in that emoji's range;
- a string field aiogram enumerates SHALL take one of its values;
- a synthesized boolean SHALL be false, and a count of an empty list zero;
- every rich media block SHALL convert.

#### Scenario: Two uploads stay apart

- **WHEN** a handler uploads two different documents with their bytes
- **THEN** the two stored documents have different file ids, and each downloads its own
  bytes

#### Scenario: A dice is a dice

- **WHEN** a handler sends a dice without an emoji several times
- **THEN** each carries 🎲 and a value from 1 to 6

#### Scenario: A sticker is a regular sticker

- **WHEN** a handler sends a sticker
- **THEN** the stored sticker's type is one of the documented types, and it is not both
  animated and a video

### Requirement: Star transactions read like Telegram's

A star transaction SHALL report the payment's charge id as its id, a positive amount, and
the user on the other side as its source or receiver.

#### Scenario: A payment and its refund

- **WHEN** a user pays and the bot refunds the charge
- **THEN** the bot's transactions report the charge id, positive amounts, and the user as
  the payment's source and the refund's receiver

### Requirement: The bot can edit the administrators it promoted

An administrator the bot promoted SHALL report `can_be_edited` as true, and others as false.

#### Scenario: A promoted member is editable by the bot

- **WHEN** the bot promotes a member and reads them back
- **THEN** the member reports `can_be_edited` true

### Requirement: A declared world matches one built through the API

What a blueprint declares SHALL read back as the same state reached through API calls:
declared permissions SHALL apply the documented defaults, declared topics SHALL be created
by the bot, and a declared poll SHALL be stored on a message in its chat.

#### Scenario: Declared permissions follow their defaults

- **WHEN** a blueprint declares a restricted member allowed to send messages
- **THEN** the member reads back allowed to react, as the same restriction through the API
  does

#### Scenario: A declared poll is stored on a message

- **WHEN** a blueprint declares a poll in a chat
- **THEN** the chat holds a message carrying that poll, and users can vote in it
