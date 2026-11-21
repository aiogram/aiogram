# Webhook Specification

## Purpose

Instead of long polling, a bot can receive updates pushed by Telegram over
HTTPS. aiogram ships aiohttp request handlers, application wiring and IP-based
protection for that mode.

## Requirements

### Requirement: aiohttp application wiring

`setup_application` SHALL bind a `Dispatcher` lifecycle to an aiohttp
`Application`.

#### Scenario: Lifecycle binding

- **WHEN** `setup_application(app, dp, bot=bot)` is called
- **THEN** dispatcher startup callbacks run on app startup and shutdown callbacks on app cleanup

### Requirement: Single-bot webhook handler

`SimpleRequestHandler` SHALL accept updates for one configured bot at a fixed
path.

#### Scenario: Registration

- **WHEN** `SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")`
- **THEN** POSTs to that path are parsed into `Update` objects and dispatched

#### Scenario: Invalid payload

- **WHEN** the request body is not valid JSON or does not validate into an `Update`
- **THEN** the error propagates out of the handler and nothing is dispatched

### Requirement: Multi-bot webhook handler

`TokenBasedRequestHandler` SHALL resolve the target bot from the `{bot_token}`
path variable, enabling one server to serve many bots.

#### Scenario: Token in path

- **WHEN** the handler is registered at `/webhook/{bot_token}` and a request arrives
- **THEN** a `Bot` for that token is created on first use, cached, and used for dispatching

#### Scenario: Path without the token placeholder

- **WHEN** `register()` is called with a path not containing `{bot_token}`
- **THEN** a `ValueError` is raised

#### Scenario: Unrecognized token

- **WHEN** the token in the path was never seen before
- **THEN** a `Bot` is still constructed for it — the handler keeps no allowlist, so access control is the caller's responsibility (a malformed token raises `TokenValidationError`)

### Requirement: Secret token verification

`SimpleRequestHandler` SHALL verify the `X-Telegram-Bot-Api-Secret-Token` header
when `secret_token` is configured. `TokenBasedRequestHandler` does not support a
secret and always accepts the header.

#### Scenario: Matching secret

- **WHEN** the header matches the configured secret
- **THEN** the update is processed

#### Scenario: Missing or wrong secret

- **WHEN** the header is absent or differs
- **THEN** the request is rejected with HTTP 401 and no update is dispatched

### Requirement: IP filtering

`IPFilter` and `ip_filter_middleware` SHALL restrict webhook access to Telegram's
published networks or an explicit allowlist.

#### Scenario: Default networks

- **WHEN** `IPFilter.default()` is used
- **THEN** only addresses inside Telegram's documented subnets are accepted

#### Scenario: Rejected address

- **WHEN** a request comes from an address outside the allowlist
- **THEN** it is rejected with HTTP 401

#### Scenario: Invalid configuration

- **WHEN** a value that is not an IPv4 address or network is allowed
- **THEN** a `ValueError` is raised

### Requirement: Answering in the webhook response

Handlers SHALL support replying to Telegram by serializing the handler's returned
method into the webhook HTTP response.

#### Scenario: Method as response

- **WHEN** a handler returns a `TelegramMethod`
- **THEN** the response is a multipart/JSON body containing that method, saving a separate API request

#### Scenario: No response

- **WHEN** the handler returns nothing
- **THEN** an empty HTTP 200 response is produced

### Requirement: Background processing mode

Handlers SHALL support dispatching updates in the background and answering
Telegram immediately, controlled by `handle_in_background` (default `True` on
both `SimpleRequestHandler` and `TokenBasedRequestHandler`).

#### Scenario: Background handling

- **GIVEN** `handle_in_background=True`
- **WHEN** an update arrives
- **THEN** an empty JSON HTTP 200 is returned immediately and the update is processed in a detached task, whose result — if it is a `TelegramMethod` — is sent as a separate request

#### Scenario: Foreground handling

- **GIVEN** `handle_in_background=False`
- **WHEN** an update arrives
- **THEN** the response is withheld until the handler finishes, so a returned method can be answered into the webhook response
