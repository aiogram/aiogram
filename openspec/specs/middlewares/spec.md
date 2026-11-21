# Middlewares Specification

## Purpose

Middlewares wrap event processing to inject dependencies, short-circuit
handling, or run cross-cutting logic. aiogram distinguishes outer middlewares
(before filters) from inner middlewares (after filters, around the handler), and
ships several built-in ones.

## Requirements

### Requirement: Middleware contract

A middleware SHALL be a `BaseMiddleware` subclass or a callable accepting
`(handler, event, data)` and SHALL decide whether and how to call the next
handler in the chain.

#### Scenario: Passing through

- **WHEN** a middleware calls `await handler(event, data)`
- **THEN** processing continues and the middleware may transform the result

#### Scenario: Short-circuit

- **WHEN** a middleware returns without calling `handler`
- **THEN** the handler is never executed

#### Scenario: Dependency injection

- **WHEN** a middleware mutates `data["session"] = db_session`
- **THEN** downstream filters and handlers can declare `session` as an argument

### Requirement: Outer and inner registration

Each observer SHALL accept both outer and inner middlewares, executed in
registration order.

#### Scenario: Outer middleware scope

- **WHEN** registered via `router.message.outer_middleware(mw)`
- **THEN** it runs for every message reaching that router, before filters are checked

#### Scenario: Inner middleware scope

- **WHEN** registered via `router.message.middleware(mw)`
- **THEN** it runs only when a handler in that router matched, wrapping the handler call

#### Scenario: Update-level middleware

- **WHEN** registered on `dp.update`
- **THEN** it wraps processing of every update regardless of type

### Requirement: Built-in user context middleware

The dispatcher SHALL resolve and expose the event's user, chat and thread in
contextual data.

#### Scenario: Resolved context

- **WHEN** any update is processed
- **THEN** `event_from_user`, `event_chat`, `event_thread_id`, `event_context` and `event_update` are present in contextual data where applicable

### Requirement: Built-in error middleware

Exceptions raised during handling SHALL be routed to `error` observers instead
of crashing the runner.

#### Scenario: Handled error

- **GIVEN** an `error` handler whose filter matches the raised exception
- **WHEN** a handler raises
- **THEN** the error handler runs and receives an `ErrorEvent` with the original update and exception

#### Scenario: Unhandled error

- **WHEN** no error handler matches
- **THEN** the exception is logged and update processing continues with the next update

### Requirement: Callback answer middleware

`CallbackAnswerMiddleware` SHALL automatically answer callback queries, driven by
handler flags.

#### Scenario: Automatic answer

- **GIVEN** the middleware is registered on the callback query observer
- **WHEN** a callback handler completes
- **THEN** `answerCallbackQuery` is sent once

#### Scenario: Flag override

- **WHEN** the handler is decorated with `@flags.callback_answer(text=..., show_alert=True)`
- **THEN** the answer uses those parameters

#### Scenario: Manual control

- **WHEN** a handler declares `callback_answer: CallbackAnswer` and mutates it
- **THEN** the mutated settings are used, and disabling it suppresses the answer

### Requirement: Chat action sender

`ChatActionMiddleware` SHALL keep a chat action alive while a flagged handler is
running.

#### Scenario: Long-running handler

- **GIVEN** a handler decorated with `@flags.chat_action("upload_document")`
- **WHEN** the handler runs longer than the configured interval
- **THEN** the chat action is re-sent periodically until the handler finishes

#### Scenario: Standalone usage

- **WHEN** `ChatActionSender.typing(bot=..., chat_id=...)` is used as an async context manager
- **THEN** the action is sent for the duration of the block
