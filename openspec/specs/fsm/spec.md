# Finite State Machine Specification

## Purpose

The FSM lets a bot hold per-user conversational state and data between updates.
It covers state declaration, the `FSMContext` API, storage backends, key
building strategies and event isolation.

## Requirements

### Requirement: State declaration

States SHALL be declared as `State` attributes of a `StatesGroup` subclass, and
SHALL resolve to a stable `"<Group>:<state>"` string.

#### Scenario: Named states

- **GIVEN** `class Form(StatesGroup): name = State()`
- **WHEN** `Form.name.state` is read
- **THEN** it equals `"Form:name"`

#### Scenario: Nested groups

- **WHEN** a `StatesGroup` subclass is nested inside another
- **THEN** its states are prefixed with the full parent group path and are included in the parent's `__all_states__`

#### Scenario: Membership check

- **WHEN** `"Form:name" in Form` is evaluated
- **THEN** it is `True`

### Requirement: FSMContext API

Handlers SHALL receive an `FSMContext` as `state` and use it to read and write
the current state and data.

#### Scenario: Setting state

- **WHEN** `await state.set_state(Form.name)` is called
- **THEN** subsequent updates for the same key resolve to that state

#### Scenario: Clearing

- **WHEN** `await state.clear()` is called
- **THEN** both the state and the data are reset

#### Scenario: Data operations

- **WHEN** `update_data`, `get_data`, `set_data` or `get_value` are used
- **THEN** the stored dictionary is merged, read, replaced or partially read respectively

### Requirement: Storage backends

The framework SHALL ship interchangeable `BaseStorage` implementations:
`MemoryStorage` (default), `RedisStorage`, `MongoStorage` (motor) and
`PyMongoStorage`.

#### Scenario: Default storage

- **WHEN** `Dispatcher()` is constructed without `storage`
- **THEN** `MemoryStorage` is used

#### Scenario: Persistent storage

- **WHEN** `RedisStorage.from_url(...)` or `MongoStorage.from_url(...)` is passed
- **THEN** state and data survive process restarts

#### Scenario: Invalid storage

- **WHEN** an object that is not a `BaseStorage` is passed
- **THEN** a `TypeError` is raised

#### Scenario: State TTL

- **GIVEN** a Redis storage configured with state/data TTL
- **WHEN** records are written
- **THEN** they expire after the configured time

### Requirement: Storage key strategies

`FSMStrategy` SHALL control how a storage key is derived from chat, user and
thread.

#### Scenario: Per user in chat

- **GIVEN** the default `USER_IN_CHAT`
- **WHEN** two users write in the same group
- **THEN** each has an independent state

#### Scenario: Per chat

- **GIVEN** `FSMStrategy.CHAT`
- **THEN** all users in the same chat share one state

#### Scenario: Global per user

- **GIVEN** `FSMStrategy.GLOBAL_USER`
- **THEN** a user shares one state across all chats

#### Scenario: Topic-aware

- **GIVEN** `USER_IN_TOPIC` or `CHAT_TOPIC`
- **THEN** the forum thread id is part of the key

### Requirement: Key building

`DefaultKeyBuilder` SHALL render storage keys from a prefix and key parts, with
optional inclusion of bot id, business connection id and destiny.

#### Scenario: Multi-bot isolation

- **GIVEN** `DefaultKeyBuilder(with_bot_id=True)`
- **WHEN** two bots serve the same user
- **THEN** their states do not collide

### Requirement: Disabling the FSM

The FSM SHALL be fully disableable for bots that do not need it.

#### Scenario: Disabled FSM

- **GIVEN** `Dispatcher(disable_fsm=True)`
- **WHEN** an update is processed
- **THEN** no storage access occurs and event isolation is inactive

### Requirement: Event isolation

The dispatcher SHALL support a pluggable `BaseEventIsolation` so that concurrent
updates for the same key are serialized when required.

#### Scenario: Default

- **WHEN** no isolation is configured
- **THEN** `DisabledEventIsolation` is used and updates are processed concurrently

#### Scenario: Locked processing

- **GIVEN** `SimpleEventIsolation` or `RedisEventIsolation`
- **WHEN** two updates for the same key arrive at once
- **THEN** the second waits until the first finishes
