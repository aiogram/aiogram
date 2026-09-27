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
Assigning a *plain mapping* SHALL still be wrapped into a fresh registry wired to this world.
Assigning another world's **live** chat registry SHALL instead be refused: a registry holds
the donor's own `ChatState` objects rather than copies, so installing it here would rewrite
`chat.world` on the objects the donor still holds, silently binding the donor's own chats —
and everything they store afterwards — to this world's bot instead. A registry already wired
to *this* world SHALL be left alone by identity, so re-assigning a world's own `chats` to
itself SHALL stay a no-op.

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

#### Scenario: Assigning another world's live registry is refused

- **WHEN** a test assigns one world's live chat registry to another world's `chats` attribute
- **THEN** the assignment raises, naming the ownership rule, and the donor's own chats stay
  wired to the donor and bound to the donor's bot

#### Scenario: Sharing chats across worlds is still possible, explicitly

- **WHEN** a test assigns a plain `dict` copy of one world's chats — `dict(other.chats)` —
  to another world's `chats` attribute
- **THEN** the same `ChatState` objects are shared, but now wired to the receiving world, and
  a chat added afterwards through either world's registry is bound to that world alone

### Requirement: A user's own private chat opens on demand

A blueprint SHALL NOT have to declare a user's private chat with the bot: every Telegram user
can open one, so the environment SHALL create it, shaped exactly as a declared one, the first
time it is needed on a *user-driven* path — when a deep link is followed, when an unbound
actor sends, when an actor binds to its own id, and when the environment's own chat accessor
is asked for the id of a *declared user* whose private chat was not itself declared. Any
*other* chat the blueprint never declared SHALL still be refused, since the world cannot
invent a group's title, type or membership from an identifier.

The bot's own calls SHALL open nothing. A real bot cannot write into a private chat first — it
may only answer a user who wrote to it — so a chat named by an outbound call and not declared
SHALL be reported as a gap in the test's setup rather than opened on demand.

#### Scenario: A followed link opens the chat

- **WHEN** a user with no declared private chat follows a start link
- **THEN** the chat exists afterwards, holds the `/start` message, and behaves like a declared
  private chat

#### Scenario: Sending from an unbound actor opens it too

- **WHEN** an actor that was never bound to a chat sends a message
- **THEN** it lands in that user's private chat with the bot

#### Scenario: The environment's chat accessor opens it too

- **WHEN** a test asks the environment's chat accessor for the id of a declared user whose
  private chat was never declared or opened
- **THEN** the chat is opened and returned, agreeing with what the actor path already does
  for that same id

#### Scenario: An undeclared group is still refused

- **WHEN** an actor binds to the identifier of a group nobody declared
- **THEN** the call raises, because the world has nothing to build that chat from

#### Scenario: The bot writing first does not open one

- **WHEN** a handler sends a message to a declared user whose private chat was never declared
  and never opened
- **THEN** the call raises rather than opening the chat, because a real bot cannot start the
  conversation

### Requirement: Per-test overrides of API results

A test SHALL be able to override the outcome of a specific method for that test only —
returning a chosen result or raising a Telegram error — and the override SHALL take
precedence over both modeling and synthesis. Overrides SHALL be scopable to a number of
calls so that consecutive calls can return different outcomes.

An override declaration SHALL be narrowable to calls of a particular shape: equality tests
on named fields of the **resolved** method — after bot-level defaults are filled in — ANDed
together, plus an arbitrary predicate for what field equality cannot say. Declaring a filter
on a field the method does not have SHALL be rejected immediately rather than registering a
rule that can never match. When more than one declared rule could answer a call, the rules
SHALL be tried in the order they were declared and the first whose shape accepts the call
SHALL win; a rule whose shape does not accept a call SHALL be left untouched by it, including
its remaining-calls budget, so an earlier call to a *different* shape cannot exhaust it.

Every override declaration SHALL return a handle that withdraws exactly the rules that
declaration registered, independently of any other declared override, and that handle SHALL
also work as a context manager scoping the override to one block.

The environment SHALL provide a named recipe for making every delivery into one chat fail
the way a real block does — covering every method that delivers content into a chat, not
only the single most common one — under the same handle-and-scoping rules as a general
override, but carrying no call-count budget: it SHALL hold for as long as it is in force
rather than for a fixed number of calls.

A call SHALL be recorded in the call log **before** any override is consulted for it, so
that a test can assert both that the call was made — reaching the right addressee with the
right content — and separately assert on how an override answered it.

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

#### Scenario: Two recipients of one trigger are given independent outcomes

- **WHEN** a test declares one outcome for `SendMessage` filtered to one chat id and another
  outcome filtered to a second chat id, and a handler messages both chats from one trigger
- **THEN** each call is answered according to the rule that names its own chat id, regardless
  of which of the two the handler happens to call first

#### Scenario: A rule that does not match is not consumed

- **WHEN** a call-limited rule is declared for one chat id, and a call is made against a
  *different* shape before a call matching the rule arrives
- **THEN** the non-matching call does not reduce the rule's remaining budget

#### Scenario: A filter on an unknown field is rejected at declaration time

- **WHEN** a test declares a field filter naming a field the method does not have
- **THEN** the declaration raises immediately, naming the fields that do exist, rather than
  registering a rule that can never match

#### Scenario: A handle withdraws only what it declared

- **WHEN** a test cancels the handle one override declaration returned
- **THEN** only the rules that declaration registered are withdrawn, and every other
  declared override is unaffected

#### Scenario: An override is scoped to a block

- **WHEN** a test uses an override's handle as a context manager around a trigger
- **THEN** the override answers calls made inside the block, and calls made after the block
  observe the default behavior again

#### Scenario: Every delivery method into a blocked chat fails

- **WHEN** a test declares the blocked-chat recipe for one chat id
- **THEN** sending, forwarding and copying into that chat all fail the way a real block fails
  them, while the same call into a *different* chat still succeeds

#### Scenario: Two recipients can be blocked independently

- **WHEN** a test declares the blocked-chat recipe for two different chat ids at once
- **THEN** both chats' deliveries fail, and a message to a third, unblocked chat still
  succeeds, regardless of which chat a handler happens to message first

#### Scenario: A refused call is still visible in the call log

- **WHEN** a call is answered by an override that raises
- **THEN** the call log still holds the call as the code under test built it, so a test can
  assert on the addressee and content of a call that was refused

### Requirement: Waiting for a condition the bot reaches on its own

The environment SHALL provide a way to wait for an arbitrary condition, re-checking it and
yielding to the event loop in between so that background work the trigger did not await can
run. The condition SHALL be allowed to be synchronous or to return an awaitable, and whatever
truthy value it produces SHALL be returned, so a wait can fetch as well as test. The wait
SHALL be satisfied immediately when the condition already holds, and SHALL NOT exceed its
stated timeout whatever polling interval it was given.

The description of what is awaited SHALL be the second **positional** parameter, since these
waits are written with lambdas and that description is the only thing a failure message can
say about one; it SHALL still be accepted as a keyword. The timing parameters SHALL stay
keyword-only.

The condition wait SHALL accept one chat or topic, or several, whose contents are appended
to the timeout message when it gives up — because the condition is a lambda over state the
failure cannot otherwise describe, while what the bot posted instead is usually the answer.

#### Scenario: A background task satisfies the wait

- **WHEN** a handler schedules work that changes the world after it returns, and the test
  waits for that change
- **THEN** the wait returns once the work has run

#### Scenario: An already-true condition costs nothing

- **WHEN** the condition holds before the wait starts
- **THEN** it returns without yielding to the event loop first

#### Scenario: The wait returns what it found

- **WHEN** the condition produces a value rather than a plain flag
- **THEN** that value is returned to the test

#### Scenario: The timeout is honored

- **WHEN** a wait is given a polling interval coarser than the time left
- **THEN** it gives up at the timeout rather than overshooting by a whole interval

#### Scenario: The description is passed without ceremony

- **WHEN** a test passes what it is waiting for as the argument after the predicate
- **THEN** a timeout quotes it, exactly as when it is passed by keyword

#### Scenario: A watched chat's contents appear in a timeout

- **WHEN** a condition wait names a chat or topic to watch and times out
- **THEN** the failure message includes that chat or topic's messages, in addition to the
  condition's own description

## ADDED Requirements

### Requirement: Routing diagnostics show where an update went

The environment SHALL report where the most recently fed update actually went, distinct
from whatever value the trigger call returned: whether the dispatcher considered it
handled, which handler and which router claimed it, and the first exception raised inside
the middleware chain or the handler — captured where it was raised even when something
further out, such as the framework's own error-handling middleware, goes on to swallow it.
"Handled" SHALL follow the dispatcher's own definition — something other than "unhandled"
came back — which a middleware that returns without calling the next one already satisfies;
the winning handler's identity SHALL be reported separately, since it is the only field
that says whether a handler actually ran. This report SHALL be cleared at the start of
every fed update and set once that update finishes routing, and SHALL be absent until the
first update is fed.

The environment SHALL also provide an assertion spelled directly against this report,
matched by a substring of the winning handler's qualified name, which SHALL fail naming
where the update actually went — including the captured exception, if there was one —
rather than only stating that the named handler did not run.

#### Scenario: A handled update names its handler and router

- **WHEN** a registered handler runs to completion for a fed update
- **THEN** the report says the update was handled and names the winning handler's qualified
  name and its router

#### Scenario: An update lost in a middleware is distinguished from one that reached a handler

- **WHEN** a middleware returns without calling the next handler in the chain
- **THEN** the report says the update was handled, since something other than "unhandled"
  came back, while naming no handler at all — the field that answers whether anything
  actually ran

#### Scenario: A catch-all handler is named rather than confused with the intended one

- **WHEN** a more specific handler's filter does not match and a catch-all handler runs
  instead
- **THEN** the report names the catch-all handler and its router, not the one the test
  expected

#### Scenario: An exception a bot's own error handler swallows is still captured

- **WHEN** a handler raises and the bot's own error handler returns a value instead of
  re-raising
- **THEN** the report still carries the original exception, captured at the handler that
  raised it, even though the trigger call itself returned normally

#### Scenario: The assertion fails naming where the update actually went

- **WHEN** a test asserts the update was handled by a name that does not match the winning
  handler
- **THEN** the failure names the handler and router that actually claimed it, including any
  captured exception

#### Scenario: The report resets between updates

- **WHEN** a second update is fed after a first one was handled
- **THEN** the report reflects only the second update's routing, not anything left over from
  the first

### Requirement: Membership triggers post the group's own join announcement

In a chat type Telegram itself shows the announcement in — a group or a supergroup — the
join and add-bot triggers SHALL also produce the `new_chat_members` service message a real
join or add delivers alongside the membership update, **after** the membership update,
matching the order Telegram's own clients display the two in. This SHALL be suppressible
per call, reverting to the previous single-update behavior. A chat type with no concept of
being "added to" — a private chat — SHALL NOT receive this service message regardless of
the setting, and a trigger that changes membership away rather than into a chat SHALL be
unaffected either way. The trigger's own return value SHALL stay the membership update's
handler result regardless of whether the service message was produced.

#### Scenario: Adding the bot to a group also posts the announcement

- **WHEN** a user actor adds the bot to a group or supergroup
- **THEN** a `my_chat_member` update is dispatched, and a `new_chat_members` message
  carrying the bot is appended to the chat after it

#### Scenario: A regular join also posts the announcement

- **WHEN** a user actor joins a group or supergroup
- **THEN** a `chat_member` update is dispatched, and a `new_chat_members` message carrying
  that user is appended to the chat after it

#### Scenario: The announcement is suppressible

- **WHEN** a join or add-bot trigger opts out of the service message
- **THEN** only the membership update is dispatched, and no message is appended to the chat

#### Scenario: A private chat never gets the announcement

- **WHEN** a user actor with no group binding triggers the equivalent of joining
- **THEN** no `new_chat_members` message is produced, regardless of the setting

#### Scenario: Leaving and removing the bot are unaffected

- **WHEN** a user actor leaves a group, or removes the bot from one
- **THEN** no `new_chat_members` message is produced

### Requirement: Actors can promote and demote chat members

Beyond the raw `promoteChatMember` call, an actor SHALL be able to promote or demote a
member directly, defaulting to promoting or demoting the bot itself — the case almost
every group bot test needs first — and otherwise accepting a declared user, a resolved
state, or a bare id as the subject. Promoting SHALL grant exactly the rights named and no
others, following the same whole-mask rule as the underlying call, but SHALL still promote
even when **no** right is named, unlike a bare call in which naming no right reads as a
demotion — there is no way through this trigger to "explicitly grant nothing." Demoting
SHALL drop the subject to a plain member and clear both the granted rights and the custom
title, while leaving the subject's tag untouched. Both SHALL refuse to act on the chat's
owner, the same refusal `promoteChatMember` itself gives.

#### Scenario: Promoting with no subject promotes the bot

- **WHEN** an actor calls the promotion trigger with no subject and at least one right
- **THEN** the bot's own membership becomes administrator, carrying exactly the rights named

#### Scenario: Promoting with no rights at all still promotes

- **WHEN** an actor calls the promotion trigger naming no rights
- **THEN** the subject becomes an administrator with every right denied, rather than being
  read as a demotion

#### Scenario: Demoting clears rights and the custom title but keeps the tag

- **WHEN** an administrator with a custom title and a tag is demoted
- **THEN** the resulting membership is a plain member with no rights and no custom title,
  and the tag is unchanged

#### Scenario: The owner cannot be promoted or demoted through this trigger

- **WHEN** the promotion or demotion trigger names the chat's owner as the subject
- **THEN** the call raises the same refusal `promoteChatMember` gives for its owner, and the
  owner's membership is unchanged

### Requirement: Sending replies is directly expressible

The send trigger SHALL accept a reply target — the message itself, or the id of one already
stored in the actor's chat — that sets the produced message's `reply_to_message`, and the
actor SHALL provide a reply trigger that is this same thing spelled as what it is. An
explicit `reply_to_message` given directly to the send trigger's other field overrides SHALL
still win, matching how those overrides win over every other field.

#### Scenario: Replying by message object

- **WHEN** an actor replies to a `Message` object already stored in its chat
- **THEN** the produced message's `reply_to_message` is that same stored object

#### Scenario: Replying by id resolves through the actor's own chat

- **WHEN** an actor replies to the id of a message already stored in its chat
- **THEN** the produced message's `reply_to_message` is the chat's own stored object under
  that id, not a copy of it

#### Scenario: An explicit field override still wins

- **WHEN** a send trigger is given both a reply target and an explicit `reply_to_message`
  field override
- **THEN** the field override is what the produced message carries

### Requirement: A misdirected click names where the button actually is

When a click trigger cannot find the named `callback_data` on any message in the actor's
own chat, and a button with that same `callback_data` exists on a message in some *other*
chat this world knows about, the failure SHALL name that chat instead of reading identically
to a click on `callback_data` that does not exist anywhere — the two are easy to conflate, a
forgotten chat binding looking exactly like a genuine typo otherwise.

#### Scenario: The failure names the chat that actually has the button

- **WHEN** an actor clicks a `callback_data` that exists on a button in a different chat
  than the one the actor is bound to
- **THEN** the failure names that other chat and points at binding the actor to it

#### Scenario: No hint is given when the button exists nowhere

- **WHEN** an actor clicks a `callback_data` that does not exist on any message in any chat
  this world knows about
- **THEN** the failure does not claim the button exists in some other chat

### Requirement: Waiting for a message across several chats at once

The environment SHALL provide a wait that polls several chats together and returns once
**every** one of them holds a matching message, rather than requiring a test to await each
chat's own message wait in turn. It SHALL accept chats named by declaration, by resolved
state, or by bare id, mixed freely, and SHALL apply the same newest-match rule a single
chat's own message wait applies. A timeout SHALL name only the chats still missing a match,
not the ones that already have one.

#### Scenario: A broadcast wait returns once every chat has a match

- **WHEN** a handler messages several chats from one trigger and a test waits across all of
  their ids at once
- **THEN** the wait returns a result keyed by chat id, once every named chat holds a message
  satisfying the predicate

#### Scenario: Mixed forms of naming a chat are accepted

- **WHEN** the chats passed to the broadcast wait mix a blueprint declaration, a resolved
  chat state and a bare id
- **THEN** all three resolve to their chats and are waited on together

#### Scenario: A timeout names only the chats still missing a match

- **WHEN** some but not all of the named chats already hold a matching message and the wait
  times out
- **THEN** the failure names only the chats that never got one, not the ones that did

### Requirement: Background tasks a test leaves running can be drained

The environment SHALL provide an explicit, opt-in way to cancel and await every task the
test itself spawned and left running — a bot's own scheduler or timer — and to report how
many there were. Only tasks created after the environment was built SHALL count as the
test's own; a task already running when the environment was built SHALL be left alone. A
task that does not finish within a stated timeout after being cancelled SHALL fail loudly
rather than being abandoned a second time. This SHALL NOT be invoked automatically by
environment teardown, since teardown has both an asynchronous and a synchronous path and an
automatic drain would behave differently between them, and since cancelling tasks a test
never mentioned as an invisible side effect of teardown would obscure a stopped background
process as a mystery rather than a stated outcome.

#### Scenario: Tasks the test left running are cancelled and awaited

- **WHEN** a trigger schedules a background task that is still running when the test asks to
  drain, with a timeout that comfortably exceeds what cancellation takes
- **THEN** the task is cancelled, awaited, and counted in the number returned

#### Scenario: A task present before the environment was built is left alone

- **WHEN** a task was already running before the environment was constructed
- **THEN** draining does not cancel it and does not count it

#### Scenario: A task that outlives its cancellation fails loudly

- **WHEN** a task swallows its own cancellation and is still running after the stated
  timeout
- **THEN** draining raises, naming the task, rather than abandoning it silently

#### Scenario: Draining is not automatic

- **WHEN** an environment with an uncancelled background task is disposed, synchronously or
  asynchronously, without draining being called
- **THEN** disposal completes without draining the task itself
