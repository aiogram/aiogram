## ADDED Requirements

### Requirement: Environment blueprint declares a reusable world

A blueprint SHALL declare the participants of a test world — chats, users, chat
memberships, the bot's own identity, and default bot properties — without creating any
mutable runtime state. A blueprint SHALL be reusable to materialize any number of
independent environments, and SHALL be usable as a module- or session-scoped value.

#### Scenario: Blueprint describes chats, users and members

- **WHEN** a test declares a blueprint with a private chat, a group chat, two users, and
  one of the users as an administrator of the group
- **THEN** every environment built from that blueprint starts with those chats, users
  and the declared membership status

#### Scenario: Blueprint is not mutated by the environments built from it

- **WHEN** two environments are built from the same blueprint and the first one sends
  messages, bans a member and pins a message
- **THEN** the second environment still reflects the blueprint's original state

#### Scenario: Blueprint supplies bot identity and defaults

- **WHEN** a blueprint declares the bot's `User` fields and `DefaultBotProperties`
- **THEN** `bot.me()` inside the environment returns the declared identity and outgoing
  API calls resolve `Default(...)` sentinels from the declared defaults

### Requirement: Environment materializes an isolated world

An environment SHALL own a `Bot` instance whose session never performs network I/O, a
`Dispatcher` supplied by the test, an FSM storage, and the mutable world state. All state
mutations SHALL be confined to that environment instance.

#### Scenario: No network traffic and no real credentials

- **WHEN** a test runs any bot flow inside an environment
- **THEN** no HTTP request is issued and no valid Telegram token is required

#### Scenario: Environment exposes the framework objects under test

- **WHEN** a test needs the `Bot`, the `Dispatcher`, or the FSM storage
- **THEN** the environment exposes each of them, and they are the same objects the
  handlers receive through dependency injection

### Requirement: Actors trigger updates through the real dispatcher

A user actor bound to a chat SHALL build a schema-valid `Update` and feed it through
`Dispatcher.feed_update`, so that filters, middlewares, dependency injection, FSM state
and routers all execute. The trigger call SHALL return the handler's return value.

#### Scenario: Sending a text message reaches the matching handler

- **WHEN** a user actor sends `"/start"` in a chat
- **THEN** the registered `/start` handler runs through the full routing pipeline and its
  return value is returned to the test

#### Scenario: Filters and middlewares are not bypassed

- **WHEN** a router declares a filter that rejects the triggered event, or a middleware
  that short-circuits it
- **THEN** the handler does not run, exactly as it would in production

#### Scenario: Extra dependencies are injected

- **WHEN** a test passes additional keyword arguments to a trigger call
- **THEN** those values are available to filters, middlewares and handlers through
  aiogram's dependency injection

#### Scenario: Identity of the event is derived from the actor

- **WHEN** a user actor bound to a group chat triggers any event
- **THEN** the resulting update carries that user as the sender and that chat as the
  chat, and `event_from_user` / `event_chat` resolve to them in handlers

### Requirement: Supported event triggers

The toolkit SHALL provide triggers for the update kinds a conversational bot needs:
sending a message, editing a message, sending media and captions, pressing an inline
keyboard button, answering an inline query, and chat member transitions (a user joining,
leaving, being promoted or banned). Each trigger SHALL produce an update indistinguishable
in shape from one Telegram would deliver.

#### Scenario: Pressing an inline keyboard button

- **WHEN** a user actor clicks a button of a message previously sent by the bot
- **THEN** a `callback_query` update is dispatched whose `data` and `message` come from
  the real button and the real stored message

#### Scenario: Chat member transition

- **WHEN** a user actor joins a group chat
- **THEN** a `chat_member` update with correct `old_chat_member` / `new_chat_member`
  statuses is dispatched, and the environment's membership state reflects the new status

#### Scenario: Editing a message sent by a user

- **WHEN** a user actor edits a message it previously sent
- **THEN** an `edited_message` update is dispatched and the stored message content changes

### Requirement: Modeled Bot API methods mutate world state

Bot API calls made by handlers SHALL be intercepted. For methods the environment models,
the call SHALL be applied to the world state and SHALL return a result consistent with
that state. Modeled methods SHALL cover at minimum: sending messages and media, editing
message text, caption and reply markup, deleting messages, forwarding and copying
messages, pinning and unpinning, answering callback queries, and chat member
administration.

#### Scenario: Sending a message appends it to the chat

- **WHEN** a handler calls `message.answer("Welcome!")`
- **THEN** a new `Message` appears in that chat's message list with the bot as sender, a
  unique `message_id`, and the resolved text

#### Scenario: Editing mutates the stored message

- **WHEN** a handler edits the text of a message the bot sent earlier
- **THEN** the stored message's text changes in place, and no additional message is added
  to the chat

#### Scenario: Deleting removes the message

- **WHEN** a handler deletes a message
- **THEN** the message is no longer present in the chat's message list, and a later
  attempt to edit it fails with the same error Telegram would return

#### Scenario: Bot-level defaults are applied before state is recorded

- **WHEN** the environment's bot declares `parse_mode="HTML"` and a handler sends a
  message without an explicit `parse_mode`
- **THEN** the recorded call and the stored message carry the resolved default

### Requirement: Unmodeled methods are recorded and answered

Any Bot API method the environment does not model SHALL still succeed by default: the
call is recorded and answered with a schema-valid result synthesized from the method's
declared return type. Synthesis SHALL derive from the generated method and type metadata,
so newly added Bot API methods work without changes to the toolkit.

#### Scenario: A method with no state semantics returns a valid object

- **WHEN** a handler calls a method the environment does not model and whose return type
  is a Bot API object
- **THEN** the call returns an instance of that type with all required fields populated,
  and the call is visible in the call log

#### Scenario: A newly added Bot API method needs no toolkit change

- **WHEN** the framework gains a new generated method and a handler calls it
- **THEN** the call succeeds with a synthesized result without any update to the testing
  package

### Requirement: Per-test overrides of API results

A test SHALL be able to override the outcome of a specific method for that test only —
returning a chosen result or raising a Telegram error — and the override SHALL take
precedence over both modeling and synthesis. Overrides SHALL be scopable to a number of
calls so that consecutive calls can return different outcomes.

#### Scenario: Overriding a result

- **WHEN** a test declares that `GetChatMember` returns a specific member object
- **THEN** every call to that method in that test returns it, regardless of world state

#### Scenario: Simulating a Telegram failure

- **WHEN** a test declares that `SendMessage` raises `TelegramForbiddenError`
- **THEN** the handler observes that exception exactly as it would in production, and the
  chat state is unchanged

#### Scenario: Overrides do not leak between tests

- **WHEN** one test overrides a method and a later test in the same module does not
- **THEN** the later test observes the default modeled or synthesized behavior

### Requirement: Call log for request assertions

The environment SHALL record every intercepted call in order and expose typed queries
over them — the last call of a type, all calls of a type, the total count, and filtering
by predicate. Recorded entries SHALL be the actual `TelegramMethod` objects, with defaults
already resolved.

#### Scenario: Asserting on the last request of a type

- **WHEN** a test asks the call log for the last `SendMessage`
- **THEN** it receives the method object whose fields can be asserted directly

#### Scenario: Asserting that a method was never called

- **WHEN** a test asserts the count of a method type is zero
- **THEN** the assertion reflects the calls made during that test only

### Requirement: Telegram errors behave like production errors

Errors produced by the environment — whether from modeling rules, from a declared
override, or from an invalid operation such as editing a deleted message — SHALL be
raised as the framework's own exception types from `aiogram.exceptions`, carrying a
description, so error handlers and `except` blocks under test behave as they do against
real Telegram.

#### Scenario: Invalid operation raises a framework exception

- **WHEN** a handler edits a message that no longer exists
- **THEN** `TelegramBadRequest` is raised with a description explaining the failure

#### Scenario: Registered error handlers receive the exception

- **WHEN** the dispatcher has an error handler and an intercepted call raises
- **THEN** the error handler runs through the normal dispatcher error pipeline

### Requirement: FSM state is inspectable and settable

The environment SHALL expose the FSM context for any user/chat pair so that a test can
assert the resulting state and data after a flow, and can arrange a starting state
without replaying the whole conversation.

#### Scenario: Asserting state after a flow

- **WHEN** a flow drives a user into a specific `State`
- **THEN** the test can read that user's current state and data from the environment

#### Scenario: Arranging a starting state

- **WHEN** a test sets a user's state and data before triggering an event
- **THEN** handlers and scenes observe that state, without the earlier steps being replayed
