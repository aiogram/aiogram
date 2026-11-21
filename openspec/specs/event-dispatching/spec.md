# Event Dispatching Specification

## Purpose

`Router` and `Dispatcher` receive Telegram updates, split them into typed events,
resolve the first matching handler through a tree of routers, and run the
resulting handler with contextual data. This capability also covers the two
runners: long polling and webhook feeding.

## Requirements

### Requirement: Event observers per update type

`Router` SHALL expose one observer per Telegram update type (`message`,
`callback_query`, `inline_query`, `chat_member`, `business_message`, … ) plus an
`error` observer, and handlers SHALL be registrable by decorator or by
`register()`.

#### Scenario: Decorator registration

- **WHEN** `@router.message(F.text)` decorates a coroutine
- **THEN** that coroutine is registered as a message handler with the given filter

#### Scenario: Imperative registration

- **WHEN** `router.message.register(handler, F.text)` is called
- **THEN** the registration is equivalent to the decorator form

### Requirement: Router tree and event propagation

Routers SHALL nest via `include_router` / `include_routers`, and an event SHALL
propagate depth-first until a handler returns anything other than `UNHANDLED`.

#### Scenario: First match wins

- **GIVEN** two handlers whose filters both pass
- **WHEN** an event is propagated
- **THEN** only the first registered handler runs

#### Scenario: Fallthrough to sub-router

- **GIVEN** the parent router has no matching handler for an event
- **WHEN** the event is propagated
- **THEN** each sub-router is tried in registration order

#### Scenario: Explicit skip

- **WHEN** a handler raises `SkipHandler`
- **THEN** propagation continues as if the handler did not match

#### Scenario: Single parent

- **WHEN** a router that already has a parent is included elsewhere
- **THEN** a `RuntimeError` is raised

#### Scenario: Self-reference

- **WHEN** a router is included into itself or into its own descendant
- **THEN** a `RuntimeError` is raised

### Requirement: Update type resolution

`Router.resolve_used_update_types()` SHALL return the sorted set of update types
that have registered handlers anywhere in the router tree, excluding internal
types (`update`, `error`).

#### Scenario: Automatic allowed_updates

- **GIVEN** only message and callback query handlers are registered
- **WHEN** polling starts without an explicit `allowed_updates`
- **THEN** `getUpdates` is called with `["callback_query", "message"]`

### Requirement: Contextual data injection

Handlers SHALL receive contextual data as keyword arguments, and SHALL only be
required to declare the arguments they actually use. The `dispatcher` argument
SHALL be present in the contextual data on every feed path — long polling,
webhook feeding and direct `feed_update`/`feed_raw_update` calls — not only
under `start_polling`.

#### Scenario: Selective arguments

- **GIVEN** the context contains `bot`, `state`, `event_from_user` and more
- **WHEN** a handler is declared as `async def h(message: Message, state: FSMContext)`
- **THEN** it is called with only those arguments

#### Scenario: Workflow data

- **WHEN** `Dispatcher(..., my_dep=obj)` is constructed or `dp["my_dep"] = obj` is set
- **THEN** `my_dep` is available to every handler and middleware

#### Scenario: Filter results in context

- **WHEN** a filter returns a dict
- **THEN** its keys are merged into the contextual data for downstream filters and the handler

#### Scenario: Dispatcher available on any feed path

- **GIVEN** a filter or handler declaring a `dispatcher: Dispatcher` parameter
- **WHEN** an update is fed through `SimpleRequestHandler`, `feed_raw_update`,
  `feed_webhook_update` or a direct `feed_update` call
- **THEN** the argument receives the `Dispatcher` instance, same as under
  `start_polling`

#### Scenario: Explicit dispatcher override wins

- **WHEN** `feed_update(bot, update, dispatcher=custom)` is called
- **THEN** filters and handlers receive `custom`, not the dispatching instance

### Requirement: Handler flags

Handlers SHALL be annotatable with arbitrary flags through the `aiogram.flags`
generator, readable by middlewares.

#### Scenario: Reading a flag

- **GIVEN** a handler decorated with `@flags.chat_action("typing")`
- **WHEN** a middleware calls `get_flag(data, "chat_action")`
- **THEN** the flag value is returned

### Requirement: Long polling runner

`Dispatcher` SHALL run one or more bots over long polling, with graceful
shutdown and backoff on network failures.

#### Scenario: Blocking runner

- **WHEN** `dp.run_polling(bot)` is called
- **THEN** the event loop is started, updates are fetched and dispatched until stopped

#### Scenario: Multiple bots

- **WHEN** several bots are passed positionally
- **THEN** each is polled concurrently against the same handler tree

#### Scenario: No bots

- **WHEN** `start_polling()` is called with no bot
- **THEN** a `ValueError` is raised

#### Scenario: Signal handling

- **GIVEN** `handle_signals=True`
- **WHEN** SIGINT or SIGTERM is received
- **THEN** polling stops gracefully and shutdown callbacks run

#### Scenario: Network backoff

- **WHEN** `getUpdates` fails with a network error
- **THEN** the request is retried with exponential backoff instead of crashing

#### Scenario: Concurrency limit

- **GIVEN** `handle_as_tasks=True` and `tasks_concurrency_limit=N`
- **WHEN** updates arrive faster than they are processed
- **THEN** at most `N` updates are processed concurrently

### Requirement: Webhook feeding

`Dispatcher` SHALL accept updates pushed from a web server and SHALL optionally
answer the webhook request with an API method call.

#### Scenario: Feeding an update

- **WHEN** `await dp.feed_update(bot, update)` or `feed_raw_update(bot, raw)` is called
- **THEN** the update is dispatched through the router tree and the handler result is returned

#### Scenario: Answering into the webhook response

- **GIVEN** a handler returns a `TelegramMethod`
- **WHEN** the update was fed via `feed_webhook_update`
- **THEN** the method is serialized into the webhook HTTP response instead of being sent as a separate request

### Requirement: Startup and shutdown hooks

Routers SHALL expose `startup` and `shutdown` observers, emitted once per run,
and SHALL receive the dispatcher workflow data.

#### Scenario: Startup callbacks

- **WHEN** the dispatcher starts
- **THEN** every registered `startup` callback across the router tree is awaited with the workflow data (including `dispatcher` and `bots`)

#### Scenario: Shutdown callbacks

- **WHEN** the dispatcher stops
- **THEN** every `shutdown` callback is awaited, and bot sessions are closed when `close_bot_session` is enabled

### Requirement: Class-based handlers

The framework SHALL provide base classes (`BaseHandler` and per-event subclasses
such as `MessageHandler`, `CallbackQueryHandler`, `ErrorHandler`) whose instances
expose the event and contextual data as attributes.

#### Scenario: Class handler execution

- **GIVEN** a subclass of `MessageHandler` implementing `handle()`
- **WHEN** it is registered on an observer and an event matches
- **THEN** an instance is created per event, `self.event` holds the message, and `handle()` is awaited
