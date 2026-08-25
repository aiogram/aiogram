## ADDED Requirements

### Requirement: Everything the world hands out carries the bot

Every object the environment gives to the code under test SHALL be bound to a `Bot` the way a
parsed Bot API response is, so that its shortcuts work — including objects nested inside a
result and the items of a list result. This SHALL hold for modeled, synthesized and overridden
results alike, and SHALL also hold for objects read directly out of the world, whoever put them
there: a message a user actor sent, and a service message produced as a side effect of a
modeled call.

#### Scenario: A shortcut on a result reaches the world

- **WHEN** a handler sends a message and calls `edit_text` on the returned `Message`
- **THEN** the edit is applied to the stored message, without the test attaching a bot by hand

#### Scenario: Nested objects and list items are bound too

- **WHEN** a result carries another object inside it, or the result is a list
- **THEN** shortcuts work on the nested object and on every item of the list

#### Scenario: A message no call returned is usable

- **WHEN** a user actor sends a message and the test reads it back out of the chat
- **THEN** calling a shortcut on it works, exactly as on a message a call returned

#### Scenario: An object the world already owns is not re-bound

- **WHEN** a second `Bot` shares the environment's session and a call through it returns a
  message the world already stored
- **THEN** that message stays bound to the environment's own bot, while objects minted for
  that call are bound to the calling bot

### Requirement: Handlers receive the world's own objects

An update SHALL arrive at the dispatcher already bound, so that the framework does not
re-create it and the object a handler receives is the object the world stores. An update
carrying objects that belong to a *different* environment SHALL be copied instead of claimed,
and the message it carries SHALL be registered in the destination chat.

#### Scenario: Identity survives the dispatcher

- **WHEN** a user actor sends a message and the handler records the `Message` it received
- **THEN** that object is the very one the chat's message list holds

#### Scenario: An update built for another environment does not act on it

- **WHEN** one update object is fed to two environments
- **THEN** the second environment answers in its own world, and the reply it sends does not
  reuse the incoming message's identifier

### Requirement: Objects a test hands to a call stay the test's own

Values the code under test passes into a Bot API call SHALL be copied before they reach world
state, so an object a test declares once — a shared `reply_markup`, a `ChatPermissions`
constant, a list of commands — is never mutated, never bound to a bot, and never keeps a
disposed environment alive. The value objects the world stores SHALL likewise be copied on the
way out. A `Message` is the deliberate exception: the message a call returns is the one the
chat holds.

#### Scenario: A shared constant is not captured by the world

- **WHEN** a test passes the same module-level `reply_markup` to a call in several tests
- **THEN** the constant is unbound and unchanged afterwards, and the world holds a copy

#### Scenario: The call log shows what the caller built

- **WHEN** a test asserts on a recorded call after the world has stored the same values
- **THEN** the recorded entry carries the values the code under test passed, not the copies
  the world went on to keep

#### Scenario: Reading state back does not bind it

- **WHEN** a handler sets chat permissions and a later `getChat` returns them
- **THEN** the returned permissions are a copy, and the permissions the world stores still
  compare equal to the constant the test declared

#### Scenario: A returned message is the stored message

- **WHEN** a handler sends a message
- **THEN** the returned `Message` is the same object the chat's message list holds

#### Scenario: A declared override result is answered fresh each time

- **WHEN** a test declares a result once and the method is called several times
- **THEN** each call is answered with its own copy, and the declared object is neither mutated
  nor left bound to any bot
