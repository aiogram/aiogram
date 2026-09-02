# Filters Specification

## Purpose

Filters decide whether a handler is applicable to an event and can enrich the
contextual data passed to it. They cover magic filters, built-in filters
(commands, states, callback data, chat member transitions, exceptions) and
user-defined filters.

## Requirements

### Requirement: Filter contract

A filter SHALL be any callable or `Filter` subclass returning a truthy/falsy
result; returning a `dict` SHALL both pass the check and inject those keys into
contextual data.

#### Scenario: Boolean filter

- **WHEN** a filter returns `False`
- **THEN** the handler is not executed and propagation continues

#### Scenario: Data-injecting filter

- **WHEN** a filter returns `{"user_id": 42}`
- **THEN** the handler may declare a `user_id` argument and receives `42`

#### Scenario: Combining filters

- **WHEN** filters are combined with `&`, `|` or `~` (or `and_f` / `or_f` / `invert_f`)
- **THEN** the combined filter evaluates with the corresponding boolean semantics

### Requirement: Magic filter

`aiogram.F` SHALL allow declarative attribute-based filtering over event objects.

#### Scenario: Attribute check

- **WHEN** `F.text` is used as a message filter
- **THEN** only messages with non-empty text match

#### Scenario: Operators

- **WHEN** `F.text.startswith("/")`, `F.chat.type == "private"` or `F.photo[-1].file_id` is used
- **THEN** the expression is resolved against the incoming event

#### Scenario: Magic on contextual data

- **WHEN** `MagicData(F.event_from_user.id == 42)` is used
- **THEN** the check is resolved against contextual data rather than the event

### Requirement: Command filter

`Command` SHALL match bot commands, honour the bot username suffix, support
prefixes, regexps and command objects, and inject a `CommandObject`.

#### Scenario: Simple command

- **WHEN** a message `/start` arrives and the handler is filtered by `Command("start")`
- **THEN** the handler runs and receives `command: CommandObject`

#### Scenario: Mentioned command in group

- **GIVEN** a message `/start@my_bot`
- **WHEN** the bot username matches
- **THEN** the command matches; a mismatched username does not match

#### Scenario: Arguments

- **WHEN** the message is `/ban 10 spam`
- **THEN** `command.args` is `"10 spam"`

#### Scenario: Deep-link start

- **WHEN** `CommandStart(deep_link=True)` is used and `/start payload` arrives
- **THEN** the handler matches and the payload is available on the command object

#### Scenario: Non-command message

- **WHEN** the message has no text or does not start with a known prefix
- **THEN** the filter does not match

### Requirement: State filter

`StateFilter` SHALL match the current FSM state, and observers SHALL apply
state filtering implicitly when a `State` is passed as a filter.

#### Scenario: Matching a state

- **GIVEN** the user is in `Form.name`
- **WHEN** a handler is registered with `Form.name` as a filter
- **THEN** it matches

#### Scenario: Any state

- **WHEN** `StateFilter("*")` is used
- **THEN** it matches regardless of the current state, including `None`

### Requirement: Callback data factory

`CallbackData` SHALL serialize and parse structured callback payloads with type
validation and SHALL provide a matching filter.

#### Scenario: Packing

- **WHEN** `MyCb(action="del", id=7).pack()` is called
- **THEN** a colon-separated string prefixed with the factory prefix is produced

#### Scenario: Filtering and unpacking

- **WHEN** a callback query with that payload arrives and the handler uses `MyCb.filter()`
- **THEN** the handler matches and receives the parsed instance as `callback_data`

#### Scenario: Partial matching

- **WHEN** `MyCb.filter(F.action == "del")` is used
- **THEN** only payloads with that field value match

#### Scenario: Invalid payload

- **WHEN** the payload does not belong to the factory or has the wrong field count
- **THEN** the filter does not match rather than raising

### Requirement: Chat member transition filter

`ChatMemberUpdatedFilter` SHALL match membership transitions using composable
status markers.

#### Scenario: Join detection

- **WHEN** the filter is `ChatMemberUpdatedFilter(JOIN_TRANSITION)`
- **THEN** it matches only updates where the user became a member

#### Scenario: Status composition

- **WHEN** markers such as `IS_ADMIN`, `IS_MEMBER`, `KICKED` are combined with `>>`, `|` or `+`
- **THEN** the resulting transition rule is applied to the old/new status pair

### Requirement: Exception filters

Error handlers SHALL be filterable by exception type and by message pattern.

#### Scenario: By type

- **WHEN** `ExceptionTypeFilter(TelegramBadRequest)` is used
- **THEN** only errors of that type (or subclasses) reach the handler

#### Scenario: By message

- **WHEN** `ExceptionMessageFilter(re.compile(r"message is not modified"))` is used
- **THEN** only matching exception messages reach the handler

### Requirement: Root filters

Filters registered on an observer via `observer.filter(...)` SHALL be evaluated
before any handler of that observer in that router.

#### Scenario: Router-wide guard

- **GIVEN** `router.message.filter(F.chat.type == "private")`
- **WHEN** a group message arrives
- **THEN** the event is reported unhandled for that whole branch — neither the router's own handlers nor its sub-routers are checked, and propagation resumes at the parent's next sibling

#### Scenario: Data injection from a root filter

- **WHEN** a root filter returns a dict
- **THEN** its keys are merged into the contextual data before handler filters run
