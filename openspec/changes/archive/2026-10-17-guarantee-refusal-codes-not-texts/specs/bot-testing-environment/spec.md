## ADDED Requirements

### Requirement: A rejection keeps its error code and exception type, not its text

Telegram guarantees no error text, so every rejection the environment emits SHALL carry an
`error_code` and raise the exception type for it: `TelegramBadRequest` for 400,
`TelegramForbiddenError` for 403 and `TelegramRetryAfter`, carrying `retry_after`, for 429.
Its description SHALL be a heuristic aid, never a contract.

#### Scenario: A rejection is matched by its type

- **WHEN** the bot sends into a group it was kicked from
- **THEN** the call raises `TelegramForbiddenError`, whatever the description says

#### Scenario: A flood says how long to wait

- **WHEN** the bot exceeds a declared rate limit
- **THEN** the call raises `TelegramRetryAfter` carrying `retry_after`

#### Scenario: A sourced description is reproduced verbatim

- **WHEN** the bot messages a user who blocked it
- **THEN** the description is `Forbidden: bot was blocked by the user`, as the Bot API server
  words it

#### Scenario: A retry_after that does not go with a 429 is refused

- **WHEN** a rejection is built with a 429 and no `retry_after`, or with `retry_after` and
  another code
- **THEN** building it raises `ValueError`

### Requirement: A rejection's description is declared once, sourced or best-effort

Each rejection SHALL be declared in `aiogram.test.rejections`. A sourced one SHALL reproduce
its description verbatim from the Bot API server, TDLib or the error lists on
core.telegram.org, and the day the sources were read SHALL be recorded once as
`SOURCES_CHECKED`. A best-effort one SHALL approximate Telegram's wording.

#### Scenario: The topic errors are sourced

- **WHEN** a test reads `rejections.TOPIC_CLOSED`
- **THEN** it is sourced from the error list of `messages.sendMessage`

#### Scenario: A rejection is not built from a literal

- **WHEN** a module of `aiogram.test` raises a rejection
- **THEN** it raises one declared in `aiogram.test.rejections`

### Requirement: A caught exception names its rejection

`rejection_of()` SHALL return the declared rejection an exception came from, and
`rejection_fields()` what its description was filled in with, so that a test tells two
rejections of one error code apart without matching their wording. An exception the
environment raised SHALL be known by identity, and any other read back against the declared
descriptions.

#### Scenario: Two rejections of one code are told apart

- **WHEN** the bot's delete is refused once because the message is not found and once because
  it cannot be deleted
- **THEN** `rejection_of()` names a different rejection each time

#### Scenario: A flood is named through aiogram's rewording

- **WHEN** a declared rate limit raises `TelegramRetryAfter`
- **THEN** `rejection_of()` names the flood rejection

### Requirement: Rejection descriptions can be perturbed

`BotTestEnvironment(perturb_rejection_descriptions=True)`, and the
`bot_env_perturb_rejection_descriptions` fixture, SHALL give every rejection a different
description with a recognisable marker, the same on every run, while keeping its error code,
its exception type and its `retry_after`. A block declared without a message SHALL be
perturbed too, and a message the test declares SHALL NOT. `rejection_of()` SHALL still name
the rejection.

#### Scenario: A bot meets a text it does not recognise

- **WHEN** the environment perturbs and the bot is refused a send into a chat it was kicked from
- **THEN** the call raises `TelegramForbiddenError` whose description does not contain `kicked`,
  and `rejection_of()` names the kicked rejection

#### Scenario: The default keeps the descriptions

- **WHEN** the environment does not perturb and the bot deletes a message that is not there
- **THEN** the description is `message to delete not found`

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

### Requirement: Topic methods check the rights of a topic that exists

A topic method SHALL check the rights only for a topic the chat has, as TDLib does for a topic
it holds; one that never existed, or was deleted, SHALL go on to the topic's own refusal. Creating
a topic SHALL take `can_manage_topics`, and so SHALL editing, closing and reopening a topic the
bot did not create and every General topic method but unpinning; deleting a topic the bot did
not create SHALL take `can_delete_messages`.

#### Scenario: The bot closes its own topic

- **WHEN** the bot, a plain member of a forum, closes a topic it created
- **THEN** the topic closes, while closing a topic someone else created raises
  `TelegramBadRequest`

#### Scenario: Deleting a topic the bot did not create

- **WHEN** a plain-member bot deletes a topic someone else created
- **THEN** the call fails with `TelegramBadRequest` for lack of `can_delete_messages`

#### Scenario: A topic that does not exist goes on to the server

- **WHEN** a plain-member bot closes a topic that does not exist
- **THEN** the call fails with `message thread not found`, whatever rights the bot holds

#### Scenario: A deleted topic loses its creator's exemption

- **WHEN** the bot deletes a topic it created and then closes it
- **THEN** the call fails with `TOPIC_DELETED`, not for lack of the right
