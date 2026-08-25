## MODIFIED Requirements

### Requirement: Routing diagnostics show where an update went

The environment SHALL report where a fed update actually went, distinct from whatever value
the trigger call returned: whether the dispatcher considered it handled, which handler and
which router claimed it, and the first exception raised inside the middleware chain or the
handler — captured where it was raised even when something further out, such as the
framework's own error-handling middleware, goes on to swallow it. "Handled" SHALL follow the
dispatcher's own definition — something other than "unhandled" came back — which a
middleware that returns without calling the next one already satisfies; the winning
handler's identity SHALL be reported separately, since it is the only field that says
whether a handler actually ran.

This diagnosis SHALL be scoped to a **trigger** rather than to a single update, because one
thing the test did is routinely more than one update: an actor trigger that produces two
updates from one call SHALL group both into the same scope, and the environment SHALL also
let a test open this scope explicitly around several trigger calls of its own. A fed update
outside any explicitly opened scope, and not itself fed from within a handler already
routing one, SHALL open a scope of its own, so the common one-update case needs no explicit
scope at all. The environment SHALL expose every record of the current scope, in the order
each finished routing, and SHALL expose the single most relevant one: the **newest handled**
record in the scope, falling back to the newest record of any kind only when nothing in the
scope was handled at all. Opening a new scope SHALL replace the previous one entirely, and
both SHALL be empty/absent until the first update is fed.

The environment SHALL also provide an assertion spelled directly against this diagnosis,
matched by a substring of the winning handler's qualified name, which SHALL scan **every**
record of the current scope — not only the most relevant one — and SHALL fail naming where
every one of them actually went, including any captured exception, rather than only stating
that the named handler did not run.

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

#### Scenario: A trigger producing several updates is diagnosed as one scope

- **WHEN** a single actor trigger delivers two updates — a membership transition and the
  chat's own announcement of it — and a handler claims one of the two while ignoring the
  other
- **THEN** both updates appear in the scope's records, and the most-relevant one names the
  update the handler actually claimed rather than whichever of the two finished routing last

#### Scenario: The assertion scans the whole scope, not only the most recent update

- **WHEN** a test asserts the current scope was handled by a name that matches only one of
  several updates fed within it
- **THEN** the assertion succeeds by finding that record among the scope's records, and a
  failure names every record in the scope, not only the last one

#### Scenario: The assertion fails naming where the update actually went

- **WHEN** a test asserts the update was handled by a name that does not match the winning
  handler
- **THEN** the failure names the handler and router that actually claimed it, including any
  captured exception

#### Scenario: The report resets between scopes

- **WHEN** a second trigger is fed after a first one was handled
- **THEN** the report reflects only the second trigger's scope, not anything left over from
  the first

### Requirement: Actors can promote and demote chat members

Beyond the raw `promoteChatMember` call, an actor SHALL be able to promote or demote a
member directly, defaulting to promoting or demoting the bot itself — the case almost
every group bot test needs first — and otherwise accepting a declared user, a resolved
state, or a bare id as the subject. Promoting SHALL grant exactly the rights named and no
others, following the same whole-mask rule as the underlying call, but SHALL still promote
even when **no** right is named, unlike a bare call in which naming no right reads as a
demotion — there is no way through this trigger to "explicitly grant nothing." A right that
is not a field of the rights model SHALL be rejected immediately, naming the fields that do
exist, rather than being silently granted to nobody. Demoting SHALL drop the subject to a
plain member and clear both the granted rights and the custom title, while leaving the
subject's tag untouched. Both SHALL refuse to act on the chat's owner as a setup error
rather than as a modeled API rejection, since a trigger arranges the world directly and asks
nothing of the intercepted call path. Both SHALL accept dispatcher data through a
keyword-only parameter distinct from the rights, so that naming a right and passing
dispatcher data are never in conflict with each other on either trigger.

#### Scenario: Promoting with no subject promotes the bot

- **WHEN** an actor calls the promotion trigger with no subject and at least one right
- **THEN** the bot's own membership becomes administrator, carrying exactly the rights named

#### Scenario: Promoting with no rights at all still promotes

- **WHEN** an actor calls the promotion trigger naming no rights
- **THEN** the subject becomes an administrator with every right denied, rather than being
  read as a demotion

#### Scenario: An unknown right is rejected at the call site

- **WHEN** an actor calls the promotion trigger naming a keyword that is not a field of the
  rights model
- **THEN** the call raises immediately, naming the fields that do exist, rather than
  promoting the subject with the misspelled right silently denied

#### Scenario: Demoting clears rights and the custom title but keeps the tag

- **WHEN** an administrator with a custom title and a tag is demoted
- **THEN** the resulting membership is a plain member with no rights and no custom title,
  and the tag is unchanged

#### Scenario: The owner cannot be promoted or demoted through this trigger

- **WHEN** the promotion or demotion trigger names the chat's owner as the subject
- **THEN** the call raises the same refusal `promoteChatMember` gives for its owner, and the
  owner's membership is unchanged

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

The environment SHALL provide a named recipe for making every call addressed at one party
fail the way a real block does, under the same handle-and-scoping rules as a general
override but carrying no call-count budget — it SHALL hold for as long as it is in force
rather than for a fixed number of calls. This SHALL cover every method that delivers content
into a chat, **and** every method that acts on content already in that chat instead of
delivering into it, since a bot's own recovery path for a failed delivery — editing,
(un)pinning or reacting to what it already sent — must be seen to fail there too; the
environment MAY name specific methods it deliberately excludes from this recipe, documenting
why, without that exclusion being a defect. The party SHALL be matchable however a call
addresses it, including by an addressing field other than the one primarily used to declare
the block, so that "this recipient" is caught whichever field the intercepted call happens
to name it with. Wherever a call's shape includes a chat-addressing field that Telegram
allows to be given either by numeric id or by `@username`, an override's declared value and
the call's actual value SHALL both be resolved through the world before comparison, so a
rule declared with one spelling still answers a call made with the other.

A call SHALL be recorded in the call log **before** any override is consulted for it, so
that a test can assert both that the call was made — reaching the right addressee with the
right content — and separately assert on how an override answered it.

The environment SHALL provide an assertion that every override currently declared on it has
answered at least one call, failing by naming each one that has not — the single most common
reason a bot behaves as though a declared override were never registered at all. The same
naming SHALL be appended to a wait's timeout message, since a never-matched override is
frequently the reason the awaited condition never became true.

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

#### Scenario: Acting on content already in the blocked chat also fails

- **WHEN** a test declares the blocked-chat recipe for one chat id, and the bot then edits,
  pins or reacts to a message already stored in that chat
- **THEN** each of those calls fails the same way a delivery into that chat fails

#### Scenario: A deliberately excluded method is unaffected by the recipe

- **WHEN** a test declares the blocked-chat recipe for one chat id, and the bot then calls a
  method the recipe documents as excluded
- **THEN** that call succeeds, and a test that wants it to fail declares that outcome itself

#### Scenario: A party addressed by a different field is still caught

- **WHEN** a test declares the blocked recipe for one party, and a call the bot makes
  addresses that same party through a field other than the one the recipe was declared
  against
- **THEN** that call still fails the way the recipe intends

#### Scenario: Two recipients can be blocked independently

- **WHEN** a test declares the blocked-chat recipe for two different chat ids at once
- **THEN** both chats' deliveries fail, and a message to a third, unblocked chat still
  succeeds, regardless of which chat a handler happens to message first

#### Scenario: An addressing field is matched by either of its spellings

- **WHEN** a call's chat-addressing field allows both a numeric id and an `@username`, and an
  override or the blocked-chat recipe is declared against one spelling
- **THEN** a call made with the other spelling of the same chat still matches, in both
  directions

#### Scenario: A refused call is still visible in the call log

- **WHEN** a call is answered by an override that raises
- **THEN** the call log still holds the call as the code under test built it, so a test can
  assert on the addressee and content of a call that was refused

#### Scenario: A never-fired override is named

- **WHEN** a test declares an override whose shape never matches any call made during the
  test, and then asks whether every declared override fired
- **THEN** the assertion fails, naming that override, rather than the test passing silently
  while the bot behaved as though the override did not exist

#### Scenario: A never-fired override is named in a wait's timeout

- **WHEN** a test declares an override that never matches any call, and a wait started after
  it times out
- **THEN** the timeout message also names that override

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
This ownership SHALL be enforced per chat, not only when the whole mapping is replaced, so
that no path into the registry — a whole-mapping assignment, an item assignment, or any of
the mapping protocol's own bulk-update operations — can register a chat that already belongs
to a *different* world without the same refusal. Registering a **fresh** chat, one that does
not yet belong to any world, SHALL always succeed: a plain mapping assigned wholesale SHALL be
wrapped into a fresh registry wired to this world, and a bare `ChatState` SHALL be adopted the
same way wherever it is registered. Registering a chat that already belongs to *this* same
world SHALL be a no-op, so re-assigning a world's own `chats` to itself, or re-registering a
chat under the id it already holds, changes nothing. Registering a chat that belongs to a
*different* world SHALL instead be refused, because a chat is not a copy the registry could
safely adopt: rewriting which world it belongs to would rewrite `chat.world` on the very
object the donor world still holds onto, silently binding the donor's own chat — and
everything it stores afterwards — to this world's bot instead, while the donor itself
observes nothing was ever reassigned. Moving a chat to a different world SHALL remain
possible, said explicitly: detaching it from its current world first, so that it is
registered here as the fresh chat it has been made to be, is one way; handing over an
independent copy of it, or one rebuilt from the same declaration, are others — none of which
require the registry itself to guess which one a test meant.

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

#### Scenario: Unwrapping a foreign registry into a plain mapping does not bypass the refusal

- **WHEN** a test assigns a plain `dict` built from one world's chats — `dict(other.chats)` —
  to another world's `chats` attribute
- **THEN** the assignment raises the same way, because each chat inside it still belongs to
  the donor world, and the donor's own chats stay wired to the donor

#### Scenario: A chat detached from its world can be moved

- **WHEN** a test removes a chat from its current world's registry, marks it as belonging to
  no world, and then registers it in a different world
- **THEN** the registration succeeds, and the chat is now wired to the new world alone

#### Scenario: A fresh chat is adopted normally

- **WHEN** a test registers a `ChatState` that has never belonged to any world
- **THEN** the registration succeeds and the chat is wired to the registering world

#### Scenario: Re-registering a chat in its own world is a no-op

- **WHEN** a test registers a chat under a world it already belongs to
- **THEN** the chat's wiring is unchanged

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

The condition wait SHALL accept one view to watch, or an iterable of several, named by
declaration, by resolved chat or topic state, or by bare chat id, mixed freely — the same
vocabulary every waiting helper that names a chat or topic accepts — whose contents are
appended to the timeout message when it gives up — because the condition is a lambda over
state the failure cannot otherwise describe, while what the bot posted instead is usually
the answer. The timeout message SHALL also name any override declared on the environment
that has not yet answered a call, since a never-matched override is frequently the reason
the condition never became true.

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

### Requirement: Waiting for a message across several chats at once

The environment SHALL provide a wait that polls several views together and returns once
**every** one of them holds a matching message, rather than requiring a test to await each
view's own message wait in turn. It SHALL accept the same vocabulary a single condition
wait's `watch=` accepts for naming what to watch — a declaration, a resolved chat or topic
state, or a bare chat id, one on its own or any iterable of them mixed freely — so that a
broadcast confined to one topic of a forum is expressible the same way a broadcast across
whole chats is. It SHALL apply the same newest-match rule a single view's own message wait
applies, and a predicate that raises on a message SHALL count as "no match" for that message
exactly as it does for a single view's own wait, with what it raised reported per view once
the wait gives up. A timeout SHALL name only the views still missing a match, not the ones
that already have one.

#### Scenario: A broadcast wait returns once every chat has a match

- **WHEN** a handler messages several chats from one trigger and a test waits across all of
  their ids at once
- **THEN** the wait returns a result keyed by chat id, once every named chat holds a message
  satisfying the predicate

#### Scenario: Mixed forms of naming a chat are accepted

- **WHEN** the chats passed to the broadcast wait mix a blueprint declaration, a resolved
  chat state and a bare id
- **THEN** all three resolve to their chats and are waited on together

#### Scenario: A broadcast wait can be confined to a topic

- **WHEN** the views passed to the broadcast wait include a forum topic rather than a whole
  chat
- **THEN** a match is required only among that topic's own messages, not the whole forum's

#### Scenario: A raising predicate is reported per view on timeout

- **WHEN** the predicate raises on a message in one of the watched views and the wait times
  out
- **THEN** the failure reports what the predicate raised for that view, the same way a single
  view's own wait reports it

#### Scenario: A timeout names only the chats still missing a match

- **WHEN** some but not all of the named chats already hold a matching message and the wait
  times out
- **THEN** the failure names only the chats that never got one, not the ones that did

### Requirement: Background tasks a test leaves running can be drained

The environment SHALL provide an explicit, opt-in way to cancel and await every task the
test itself spawned and left running — a bot's own scheduler or timer — and to report how
many there were. Only tasks created after the environment was built SHALL count as the
test's own; a task already running SHALL be left alone. Because the environment's
construction may happen with no event loop running at all, "already running" SHALL be
established as of this environment's first asynchronous action if that comes later than
construction, so that a task belonging to another, wider-scoped fixture — one already alive
by the time this environment's own tasks could possibly begin — is spared regardless of
whether the environment could observe it at construction time. A task that does not finish
within a stated timeout after being cancelled SHALL fail loudly rather than being abandoned
a second time. A task that ends with anything other than the cancellation it was sent SHALL
also fail loudly, distinctly from a task that merely failed to finish in time, naming every
such task and preserving the original failure so it can be inspected rather than only
noted. This SHALL NOT be invoked automatically by environment teardown, since teardown has
both an asynchronous and a synchronous path and an automatic drain would behave differently
between them, and since cancelling tasks a test never mentioned as an invisible side effect
of teardown would obscure a stopped background process as a mystery rather than a stated
outcome.

#### Scenario: Tasks the test left running are cancelled and awaited

- **WHEN** a trigger schedules a background task that is still running when the test asks to
  drain, with a timeout that comfortably exceeds what cancellation takes
- **THEN** the task is cancelled, awaited, and counted in the number returned

#### Scenario: A task present before the environment was built is left alone

- **WHEN** a task was already running before the environment was constructed
- **THEN** draining does not cancel it and does not count it

#### Scenario: A task belonging to a wider-scoped fixture is spared even without a running loop at construction

- **WHEN** the environment is constructed synchronously with no event loop running, a task
  from a wider-scoped fixture is already running by the time this environment first acts
  asynchronously, and the test then asks to drain
- **THEN** draining does not cancel that task, exactly as if it had been running at
  construction

#### Scenario: A task that outlives its cancellation fails loudly

- **WHEN** a task swallows its own cancellation and is still running after the stated
  timeout
- **THEN** draining raises, naming the task, rather than abandoning it silently

#### Scenario: A task that fails on its own is reported rather than silently retrieved

- **WHEN** a drained task ends with an exception of its own rather than with the
  cancellation it was sent
- **THEN** draining raises, naming that task and preserving its original failure, rather
  than treating it the same as a task that was simply cancelled on time

#### Scenario: Draining is not automatic

- **WHEN** an environment with an uncancelled background task is disposed, synchronously or
  asynchronously, without draining being called
- **THEN** disposal completes without draining the task itself
