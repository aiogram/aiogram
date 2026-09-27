## MODIFIED Requirements

### Requirement: Everything the world hands out carries the bot

Every object the environment gives to the code under test SHALL be bound to a `Bot` the way
a parsed Bot API response is, so that its shortcuts work — including objects nested inside a
result and the items of a list result. This SHALL hold for modeled, synthesized and
overridden results alike, and SHALL also hold for objects read directly out of the world,
whoever put them there: a message a user actor sent, and a service message produced as a
side effect of a modeled call.

An object that already carries a bot belongs to whoever owns it and SHALL NOT be re-bound,
so a second `Bot` sharing the environment's session never takes over the world's own
objects.

The binding SHALL be a property of the world's chat registry rather than of one moment in its
life: a chat SHALL be wired to its world however it is registered, including when the whole
mapping is replaced after construction, so that messages stored afterwards are bound as usual.
This SHALL hold even when the replacement mapping is itself another world's chat registry:
assigning it SHALL install a registry wired to *this* world rather than reusing the donor's,
so a chat later added through it is bound to this world's bot and not the donor's.

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

#### Scenario: Replacing the chat mapping does not detach the world

- **WHEN** a test assigns a plain mapping of chats to the world after it was built
- **THEN** those chats are wired to the world as declared ones are, and messages stored in
  them afterwards carry the bot

#### Scenario: Assigning another world's registry does not carry its wiring along

- **WHEN** a test assigns one world's chat registry to another world's `chats` attribute
- **THEN** the assignment installs a registry wired to the receiving world, and a chat added
  through it afterwards is bound to the receiving world's bot rather than the donor's

### Requirement: Handlers receive the world's own objects

An update SHALL arrive at the dispatcher already bound, so that the framework does not
re-create it and the object a handler receives is the object the world stores. An update
carrying objects that belong to a *different* environment SHALL be copied instead of
claimed, and the message it carries SHALL be registered in the destination chat.

Registering a carried message whose id is already taken by a *different* message in the
destination chat SHALL raise `WorldLookupError` naming both messages, rather than silently
keeping the one already there — a handler reacting to the incoming update would otherwise work
on a message the world never stores, and a `wait_for_message` waiting for it would wait
forever with nothing to explain why. Registering one whose id is taken by an equal message —
the same update fed again, or an equal one built the same way twice — SHALL stay the silent
no-op it always was.

#### Scenario: Identity survives the dispatcher

- **WHEN** a user actor sends a message and the handler records the `Message` it received
- **THEN** that object is the very one the chat's message list holds

#### Scenario: An update built for another environment does not act on it

- **WHEN** one update object is fed to two environments
- **THEN** the second environment answers in its own world, and the reply it sends does not
  reuse the incoming message's identifier

#### Scenario: A carried message id colliding with a different message is refused

- **WHEN** an update carries a message whose id is already taken in the destination chat by a
  message with different content
- **THEN** registering it raises `WorldLookupError` describing both the message already there
  and the incoming one, rather than silently discarding the incoming one

#### Scenario: Re-registering an equal carried message is still a no-op

- **WHEN** an update carrying a message equal to one already registered under the same id is
  fed again
- **THEN** no error is raised and the chat's state is unchanged
