# Bot Client Specification

## Purpose

`aiogram.Bot` is the single entry point for calling the Telegram Bot API. It owns
a pluggable HTTP session, applies default bot properties to outgoing calls,
resolves API server endpoints, downloads files, and maps API errors onto typed
exceptions.

## Requirements

### Requirement: Bot instantiation and token validation

`Bot` SHALL be constructed from a bot token and SHALL reject malformed tokens at
construction time.

#### Scenario: Valid token

- **WHEN** `Bot(token="42:TEST")` is constructed
- **THEN** the instance is created and `bot.id` returns `42`

#### Scenario: Malformed token

- **WHEN** a token that does not match `<id>:<secret>` is passed
- **THEN** a `TokenValidationError` is raised

### Requirement: API method invocation

`Bot` SHALL expose a typed method for every Bot API method and SHALL also accept
method objects directly via `await bot(method)`.

#### Scenario: Shortcut call

- **WHEN** `await bot.send_message(chat_id=1, text="hi")` is called
- **THEN** the corresponding `SendMessage` method object is built and sent through the session
- **AND** the parsed `Message` is returned bound to the calling bot

#### Scenario: Method object call

- **WHEN** `await bot(SendMessage(chat_id=1, text="hi"))` is called
- **THEN** the result is identical to the shortcut form

#### Scenario: Per-request timeout

- **WHEN** `request_timeout` is passed to a call
- **THEN** it overrides the session-level timeout for that request only

### Requirement: Default bot properties

`Bot` SHALL accept `DefaultBotProperties` and SHALL substitute those values into
outgoing method fields whose value is the sentinel `Default(...)`.

#### Scenario: Default parse mode applied

- **GIVEN** `Bot(token, default=DefaultBotProperties(parse_mode="HTML"))`
- **WHEN** a message is sent without an explicit `parse_mode`
- **THEN** the request carries `parse_mode="HTML"`

#### Scenario: Explicit value wins

- **WHEN** a call passes `parse_mode="MarkdownV2"` explicitly
- **THEN** the default is not applied

### Requirement: Pluggable HTTP session

The transport SHALL be an implementation of `BaseSession`, defaulting to
`AiohttpSession`, and SHALL be replaceable without changing call sites.

#### Scenario: Custom session

- **WHEN** a `Bot` is constructed with `session=AiohttpSession(proxy=...)`
- **THEN** all API requests are issued through that session

#### Scenario: Session middleware

- **WHEN** a callable is registered via `session.middleware`
- **THEN** it wraps every outgoing API request and can inspect or modify the call

#### Scenario: Session lifecycle

- **WHEN** `async with bot:` is used or `await bot.session.close()` is called
- **THEN** underlying connections are released

### Requirement: Telegram API server configuration

The framework SHALL support the production server, the test server, and
self-hosted local Bot API servers via `TelegramAPIServer`.

#### Scenario: Local Bot API server

- **GIVEN** `TelegramAPIServer.from_base("http://localhost:8081", is_local=True)`
- **WHEN** the bot downloads a file
- **THEN** the local filesystem path is used, translated through the configured `FilesPathWrapper`

### Requirement: File downloading

`Bot` SHALL download files by `file_id` or `File` object, to a destination path
or to an in-memory binary stream.

#### Scenario: Download to path

- **WHEN** `await bot.download(file_id, destination="a.jpg")` is called
- **THEN** the file content is written to that path

#### Scenario: Download to memory

- **WHEN** `destination` is omitted
- **THEN** a `BinaryIO` positioned at the start is returned

### Requirement: Typed API error mapping

Non-success API responses SHALL be raised as specific subclasses of
`TelegramAPIError` carrying the originating method.

#### Scenario: Response parameters take precedence

- **WHEN** the error response carries `parameters.retry_after` or `parameters.migrate_to_chat_id`
- **THEN** `TelegramRetryAfter` or `TelegramMigrateToChat` is raised with that value, regardless of the HTTP status code

#### Scenario: Error classification

- **WHEN** the API responds `400` / `401` / `403` / `404` / `409` / `413` / `5xx`
- **THEN** `TelegramBadRequest` / `TelegramUnauthorizedError` / `TelegramForbiddenError` / `TelegramNotFound` / `TelegramConflictError` / `TelegramEntityTooLarge` / `TelegramServerError` is raised respectively

#### Scenario: Server restart

- **WHEN** a `5xx` response description mentions a restart
- **THEN** `RestartingTelegram` is raised instead of `TelegramServerError`

#### Scenario: Unclassified status

- **WHEN** the response is unsuccessful with any other status code
- **THEN** the base `TelegramAPIError` is raised

#### Scenario: Undecodable response

- **WHEN** the response body is not valid JSON, or does not validate into the method's return type
- **THEN** `ClientDecodeError` is raised with the original payload attached

### Requirement: Bot context binding

Telegram objects returned by the API SHALL be bound to the `Bot` that produced
them, so object shortcuts work without passing a bot explicitly.

#### Scenario: Shortcut on a received object

- **WHEN** `await message.answer("text")` is called on a message received from an update
- **THEN** the call is dispatched through the bot bound to that message

#### Scenario: Rebinding

- **WHEN** `obj.as_(other_bot)` is called
- **THEN** subsequent shortcuts on `obj` use `other_bot`
