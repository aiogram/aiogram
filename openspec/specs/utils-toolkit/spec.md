# Utilities Toolkit Specification

## Purpose

`aiogram.utils` collects the helpers that make everyday bot code short:
keyboard builders, rich text formatting, deep links, media groups, Web App data
verification and small runtime helpers.

## Requirements

### Requirement: Keyboard builders

`InlineKeyboardBuilder` and `ReplyKeyboardBuilder` SHALL build keyboard markup
incrementally with automatic row layout.

#### Scenario: Adding buttons

- **WHEN** `builder.button(text=..., callback_data=...)` or `builder.add(button)` is called
- **THEN** the button is appended to the current markup

#### Scenario: Layout control

- **WHEN** `builder.adjust(2, 3)` is called
- **THEN** buttons are re-flowed into rows of the given widths, and `repeat=True` cycles the pattern for the remaining buttons

#### Scenario: Explicit rows

- **WHEN** `builder.row(*buttons)` is used
- **THEN** those buttons form their own row regardless of the current width

#### Scenario: Composition

- **WHEN** `builder.attach(other_builder)` is used
- **THEN** the other builder's rows are appended

#### Scenario: Export

- **WHEN** `builder.as_markup()` is called
- **THEN** an `InlineKeyboardMarkup` / `ReplyKeyboardMarkup` ready to send is returned

#### Scenario: Wrong button type

- **WHEN** a reply button is added to an inline builder
- **THEN** a `ValueError` is raised

### Requirement: Rich text formatting

`aiogram.utils.formatting` SHALL compose styled text as a node tree and render it
either to entities or to HTML/Markdown, and SHALL parse existing entities back
into that tree.

#### Scenario: Composing

- **WHEN** `Text("hi ", Bold("world"))` is built
- **THEN** `as_kwargs()` returns text plus `entities` suitable for a send call

#### Scenario: Layout helpers

- **WHEN** `as_list`, `as_marked_list`, `as_numbered_list`, `as_section` or `as_key_value` are used
- **THEN** the corresponding multi-line structure is produced

#### Scenario: Round-trip

- **WHEN** `Text.from_entities(text, entities)` is called on a received message
- **THEN** an equivalent node tree is produced

### Requirement: Text decorations

`aiogram.html` and `aiogram.md` SHALL escape and wrap text in the respective
markup, and SHALL be able to unparse a message's entities.

#### Scenario: Escaping

- **WHEN** user input containing `<` or `*` is wrapped with `html.bold(...)` / `md.bold(...)`
- **THEN** the special characters are escaped so the resulting markup stays valid

#### Scenario: Unparsing

- **WHEN** `html.unparse(text, entities)` is called
- **THEN** the original formatted text is reconstructed

### Requirement: Deep links

Helpers SHALL build `t.me` deep links with optional payload encoding.

#### Scenario: Start link

- **WHEN** `await create_start_link(bot, "ref-123")` is called
- **THEN** a `https://t.me/<username>?start=ref-123` link is returned

#### Scenario: Group and app links

- **WHEN** `create_startgroup_link` or `create_startapp_link` is used
- **THEN** the corresponding parameter is used instead of `start`

#### Scenario: Encoded payload

- **WHEN** `encode=True` is passed
- **THEN** the payload is base64url-encoded and can be restored with `decode_payload`

#### Scenario: Payload limits

- **WHEN** the payload exceeds the allowed length or contains unsupported characters
- **THEN** a `ValueError` is raised

### Requirement: Media group builder

`MediaGroupBuilder` SHALL assemble a valid album payload.

#### Scenario: Building

- **WHEN** `add_photo`, `add_video`, `add_audio` or `add_document` are called and `build()` is invoked
- **THEN** a list of `InputMedia*` objects is returned with the caption applied to the first item

#### Scenario: Unknown media type

- **WHEN** `add(type="unknown", ...)` is called
- **THEN** a `ValueError` is raised

### Requirement: Web App data verification

Telegram Web App `initData` SHALL be verifiable and parseable.

#### Scenario: Valid signature

- **WHEN** `check_webapp_signature(token, init_data)` is called with authentic data
- **THEN** it returns `True`, and `parse_webapp_init_data` returns a `WebAppInitData`

#### Scenario: Tampered data

- **WHEN** the data was modified
- **THEN** `check_webapp_signature` returns `False`, `parse_webapp_init_data` raises, and `safe_parse_webapp_init_data` raises `ValueError`

### Requirement: Login widget verification

Telegram Login Widget payloads SHALL be verifiable against the bot token.

#### Scenario: Authentic payload

- **WHEN** `check_signature(token, hash, **data)` is called with an authentic payload
- **THEN** it returns `True`

### Requirement: Chat and user link helpers

Helpers SHALL produce user and message links.

#### Scenario: User link

- **WHEN** `create_tg_link` / `create_telegram_link` helpers are used
- **THEN** a valid `tg://` or `https://t.me/` URL is produced

### Requirement: Network backoff

`Backoff` and `BackoffConfig` SHALL provide exponential retry delays with jitter,
used by the polling runner.

#### Scenario: Growing delay

- **WHEN** consecutive failures occur
- **THEN** the delay grows by the configured factor up to `max_delay`

#### Scenario: Reset

- **WHEN** a successful attempt occurs and `reset()` is called
- **THEN** the next delay starts from `min_delay` again
