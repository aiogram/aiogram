## ADDED Requirements

### Requirement: A refusal guarantees its error code and exception type, not its text

Every refusal the environment emits SHALL carry an `error_code` and raise the exception type
for it: `TelegramBadRequest` for 400, `TelegramForbiddenError` for 403 and `TelegramRetryAfter`,
carrying `retry_after`, for 429. Its description SHALL be best-effort, except for the texts
documented as guaranteed, which are Telegram's own.

#### Scenario: A refusal is matched by its type

- **WHEN** the bot sends into a group it was kicked from
- **THEN** the call raises `TelegramForbiddenError`, whatever the description says

#### Scenario: A flood says how long to wait

- **WHEN** the bot exceeds a declared rate limit
- **THEN** the call raises `TelegramRetryAfter` carrying `retry_after`

#### Scenario: A guaranteed text is Telegram's own

- **WHEN** the bot messages a user who blocked it
- **THEN** the description is `Forbidden: bot was blocked by the user`

#### Scenario: Only Telegram's own texts are guaranteed

- **WHEN** a test reads the guaranteed texts
- **THEN** they are `bot was blocked by the user`, `bot was kicked from the … chat`,
  `bot is not a member of the … chat`, `message to edit not found`,
  `message to delete not found`, `message to be replied not found`, `message thread not
  found`, `query is too old and response timeout expired or query ID is invalid`,
  `can't parse entities: …` and `retry after …`

#### Scenario: A code the type cannot stand for is refused

- **WHEN** a refusal is built with a code other than 400, 403 or 429, or a 429 without
  `retry_after`
- **THEN** building it raises `ValueError`

### Requirement: A refusal's text is declared once, sourced or best-effort

Each refusal SHALL be declared in `aiogram.test.refusals`, marked sourced, when its text comes
from the Bot API server or TDLib, or best-effort. Only a sourced text SHALL be guaranteed.

#### Scenario: A guaranteed text cites a source

- **WHEN** a refusal is declared guaranteed without a source
- **THEN** declaring it raises `ValueError`

## MODIFIED Requirements

### Requirement: Telegram errors behave like production errors

A call the real Bot API would refuse SHALL fail the way it fails in production: the
framework's own exception types from `aiogram.exceptions`, raised through the session's own
response check, whether the refusal comes from a modeling rule, from a declared override, or
from an invalid operation such as editing a deleted message. So an `except` branch in the bot
under test is exercised exactly as it would be against real Telegram.

#### Scenario: Invalid operation raises a framework exception

- **WHEN** a handler edits a message that no longer exists
- **THEN** `TelegramBadRequest` is raised

#### Scenario: Registered error handlers receive the exception

- **WHEN** the dispatcher has an error handler and an intercepted call raises
- **THEN** the error handler runs through the normal dispatcher error pipeline

#### Scenario: A handler can catch the refusal itself

- **WHEN** a handler wraps a call in `except TelegramBadRequest`
- **THEN** it catches the refusal

### Requirement: Topic methods check the rights before the topic is looked up

A topic method SHALL check the rights before it looks the topic up. Creating a topic SHALL
take `can_manage_topics`, and so SHALL editing, closing and reopening a topic the bot did
not create and every General topic method but unpinning; deleting a topic the bot did not
create SHALL take `can_delete_messages`.

#### Scenario: The bot closes its own topic

- **WHEN** the bot, a plain member of a forum, closes a topic it created
- **THEN** the topic closes, while closing a topic someone else created raises
  `TelegramBadRequest` with `not enough rights to close or open the topic`

#### Scenario: Deleting a topic the bot did not create

- **WHEN** a plain-member bot deletes a topic someone else created
- **THEN** the call fails for lack of `can_delete_messages`

#### Scenario: Rights are checked before the topic is looked up

- **WHEN** a plain-member bot closes a topic that does not exist
- **THEN** the call fails for lack of rights rather than for the missing topic

#### Scenario: A bot with the right meets the missing topic

- **WHEN** a bot holding `can_manage_topics` closes a topic that does not exist
- **THEN** the call fails with `message thread not found`
