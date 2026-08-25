## MODIFIED Requirements

### Requirement: Telegram errors behave like production errors

A call the real Bot API would refuse SHALL fail the way it fails in production: the framework's
own exception types from `aiogram.exceptions`, raised through the session's own response check,
carrying Telegram's wording — whether the refusal comes from a modeling rule, from a declared
override, or from an invalid operation such as editing a deleted message. So an `except` branch
in the bot under test is exercised exactly as it would be against real Telegram.

#### Scenario: Invalid operation raises a framework exception

- **WHEN** a handler edits a message that no longer exists
- **THEN** `TelegramBadRequest` is raised with a description explaining the failure

#### Scenario: Registered error handlers receive the exception

- **WHEN** the dispatcher has an error handler and an intercepted call raises
- **THEN** the error handler runs through the normal dispatcher error pipeline

#### Scenario: A handler can catch the refusal itself

- **WHEN** a handler wraps a call in `except TelegramBadRequest`
- **THEN** it catches the refusal and reads Telegram's own wording out of it

## ADDED Requirements

### Requirement: A gap in the test's own setup fails the test, not the bot

A refusal caused by something the blueprint never declared, or by a surface the toolkit does not
model, SHALL be raised as a distinct error type that the environment never converts into a
Telegram error. It SHALL propagate out of the call the bot made and fail the test, so the bot's
own error handling cannot swallow it and leave a green test that exercised the wrong branch.
Its message SHALL say what to declare or how to proceed.

The two kinds SHALL be distinguishable by type: a modeled rejection is something Telegram itself
would answer, while a setup gap is not.

#### Scenario: An undeclared entity is not reported as a Bad Request

- **WHEN** a handler calls a method naming a user, chat, sticker set, poll, gift, charge or
  business connection the blueprint never declared
- **THEN** the call raises the setup-gap error rather than `TelegramBadRequest`, and the message
  names what is missing

#### Scenario: The bot's own error handling cannot hide it

- **WHEN** the bot under test wraps its calls in `except TelegramBadRequest`
- **THEN** a setup gap still reaches the test, because it is not a Telegram error

#### Scenario: Something the toolkit does not model says so

- **WHEN** a handler edits a message addressed by `inline_message_id`
- **THEN** the call raises the setup-gap error naming inline messages as unmodeled, rather than
  claiming Telegram refused it

#### Scenario: Reaching into the world directly surfaces the rejection unconverted

- **WHEN** a test asks a chat for a message or a topic that is not there, outside any call
- **THEN** the modeled rejection is raised as it is, since there is no call to convert it into a
  Telegram error
