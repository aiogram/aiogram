# Bot API Layer & Codegen Specification

## Purpose

`aiogram.types`, `aiogram.methods` and `aiogram.enums` mirror the Telegram Bot
API one-to-one. They are **generated** by the `butcher` tool from `.butcher/`
inputs, so keeping the framework current with a new Bot API version is a
regeneration task, not a hand-editing task.

## Requirements

### Requirement: Full Bot API coverage

Every Bot API object, method and enumeration of the supported API version SHALL
have a corresponding generated class.

#### Scenario: Version marker

- **WHEN** `aiogram.__api_version__` is read
- **THEN** it reports the Bot API version the package targets

#### Scenario: New API entity

- **WHEN** Telegram adds an object or method
- **THEN** a matching class appears under `aiogram/types` or `aiogram/methods` after regeneration, with typed fields and docstrings linking to the official docs

### Requirement: Pydantic-backed models

Telegram objects SHALL be pydantic models with validation, aliasing and
serialization of the Bot API wire format.

#### Scenario: Parsing

- **WHEN** a raw API payload is validated into a type
- **THEN** nested objects are constructed recursively and unknown fields are tolerated

#### Scenario: Serialization

- **WHEN** a method object is serialized for a request
- **THEN** unset fields are omitted and enums are rendered as their values

### Requirement: Method objects are callable

Every Bot API method SHALL be representable as an object that can be awaited
through a bot, returned from a handler, or built via the corresponding `Bot`
shortcut.

#### Scenario: Returning from a handler

- **WHEN** a handler returns `SendMessage(chat_id=..., text=...)`
- **THEN** the dispatcher sends it (or answers the webhook with it)

### Requirement: Object shortcuts

Telegram objects SHALL expose ergonomic shortcuts that prefill ids from the
object itself.

A prefilled value that is derived by more than a plain attribute access SHALL be
produced by a named method on the object rather than by an expression inlined into
each generated shortcut, so that the rule has one definition and can be called
directly by users.

A shortcut SHALL only prefill a parameter that its target method declares.

#### Scenario: Message shortcuts

- **WHEN** `message.answer(...)`, `message.reply(...)`, `message.delete()` or `message.edit_text(...)` is called
- **THEN** `chat_id` / `message_id` are taken from the message

#### Scenario: Callback query shortcut

- **WHEN** `callback_query.answer(...)` is called
- **THEN** `callback_query_id` is filled automatically

#### Scenario: Reply parameters are built by a named method

- **WHEN** any `message.reply_*(...)` shortcut is called
- **THEN** `reply_parameters` is the result of `message.as_reply_parameters()`

#### Scenario: Ephemeral parameters are built by a named method

- **WHEN** a `message.reply_*(...)` shortcut whose method accepts `ephemeral_message_parameters` is called
- **THEN** that argument is the result of `message.as_ephemeral_message_parameters()`

#### Scenario: Shortcut does not prefill an undeclared parameter

- **WHEN** `message.reply_dice()`, `message.reply_poll(...)`, `message.reply_game(...)`, `message.reply_invoice(...)`, `message.reply_media_group(...)` or `message.reply_paid_media(...)` is called on an ephemeral message
- **THEN** the resulting method object carries no `ephemeral_message_parameters`, in its fields or in its extras

### Requirement: Input file abstractions

Uploading files SHALL be supported from disk, memory, a URL or an existing
`file_id`.

#### Scenario: Local file

- **WHEN** `FSInputFile("photo.jpg")` is passed
- **THEN** the file is streamed as multipart form data

#### Scenario: In-memory and streamed files

- **WHEN** `BufferedInputFile(...)` or `URLInputFile(...)` is passed
- **THEN** the content is uploaded from the buffer or fetched and streamed respectively

### Requirement: Generation is the source of truth

Generated modules SHALL NOT be hand-edited; changes SHALL be made to `.butcher`
inputs (schema, aliases, templates) and applied via the generator.

#### Scenario: Adding a shortcut

- **WHEN** a new object shortcut is needed
- **THEN** it is declared in the relevant `.butcher/**/*.yml` and produced by `butcher apply`, not written directly into `aiogram/types`

#### Scenario: Regeneration flow

- **WHEN** the API is bumped
- **THEN** `butcher parse`, `butcher refresh` and `butcher apply all` are run, followed by lint, type checks and tests

#### Scenario: Parser artifacts

- **WHEN** `.butcher/**/entity.json` differs from expectations
- **THEN** it is regenerated rather than edited, since the parser overwrites it

### Requirement: Changelog for API updates

A Bot API version bump SHALL be accompanied by a changelog fragment describing
the user-visible additions.

#### Scenario: API bump PR

- **WHEN** a Bot API update branch is prepared
- **THEN** `CHANGES/<issue>.misc.rst` summarizes the new objects, methods and fields

### Requirement: Ephemeral message parameters helper

`Message` SHALL expose `as_ephemeral_message_parameters()`, which builds the
`EphemeralMessageParameters` object describing who an ephemeral reply is addressed
to.

The helper SHALL accept `callback_query_id` and `replace_callback_query_message` as
optional keyword arguments, since neither value is derivable from a `Message`.

#### Scenario: Called on an ephemeral message

- **WHEN** `message.as_ephemeral_message_parameters()` is called and the message has an `ephemeral_message_id` and a sender
- **THEN** an `EphemeralMessageParameters` is returned whose `receiver_user_id` is the sender's id

#### Scenario: Called on a regular message

- **WHEN** `message.as_ephemeral_message_parameters()` is called and the message has no `ephemeral_message_id`
- **THEN** `None` is returned, so a shortcut that prefills it sends nothing

#### Scenario: Optional callback query fields

- **WHEN** `message.as_ephemeral_message_parameters(callback_query_id="q1", replace_callback_query_message=True)` is called on an ephemeral message
- **THEN** both values appear on the returned object
