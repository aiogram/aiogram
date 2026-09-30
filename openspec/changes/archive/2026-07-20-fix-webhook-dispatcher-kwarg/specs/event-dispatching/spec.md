# Event Dispatching — delta

## MODIFIED Requirements

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
