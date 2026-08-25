## Context

`BotContextController` is aiogram's own mechanism: a model that carries a bot can call
shortcuts, and a model that does not raises. The real session never binds anything by hand —
it validates the response with `context={"bot": bot}` and pydantic threads the context through
the entire tree. The fake has no response to validate: it builds `Message` objects out of
world state, hands out ones it stored earlier, and synthesizes the rest.

So the toolkit needs its own answer to "who owns this object", and it needs one answer rather
than one per producer. Before this change there was none, and the symptom list was long and
looked unrelated: shortcuts raising on results, shortcuts raising on stored messages, handlers
receiving copies, a shared constant silently changing identity mid-suite.

## Goals / Non-Goals

**Goals:**

- Every object the code under test can reach has a bot, so every shortcut works.
- The object a handler receives *is* the object the world stores.
- Nothing the test built ends up in the world, and nothing the world stores ends up bound
  into the test's own constants.
- One mechanism, at choke points, rather than a rule each handler has to remember.

**Non-Goals:**

- Deep-copying everything. A copy at every hop would be simple to explain and would destroy
  the identity that makes state assertions worth writing.
- Modelling pydantic's validation context faithfully. What is needed is the *effect* of the
  context, not the machinery.
- Making objects with different owners compare equal. That is pydantic's rule, shared with
  production; the toolkit only explains it when it bites.

## Decisions

### D1. Walk the graph and call `as_()`, rather than re-parsing

Binding by round-tripping through `model_dump()` / `model_validate(..., context=...)` was the
obvious first idea, and it is the one that reuses aiogram's own mechanism. It was rejected.

Pydantic skips validation of model instances (`revalidate_instances` is `"never"`), so binding
that way requires a genuine dump/validate round-trip — which **mints copies**. That severs the
identity between a returned message and the one the world keeps, which is the single property
this whole change exists to establish, and it quietly reshapes unions and sentinel defaults on
the way through. pydantic-core's serializer also gives up on a deep graph, reporting the depth
as a circular reference.

`bindables()` walks the tree and calls `BotContextController.as_(bot)` on each node, which is
exactly what the context does, and leaves the objects themselves untouched.

The walk is **iterative**, not recursive. A `reply_to_message` chain is as long as a test cares
to make it, and a recursive walker hit Python's recursion limit on chains a real test builds.

### D2. Bind on the way *in*, at `ChatState.add_message`

Mounting results as they leave a call fixes results only. A message a user actor sent, or a
service message a modeled call produced as a side effect, is never any call's result — and
`chat.messages[-1].answer(...)` is exactly what a state-based test writes next.

Storage is the one moment every producer shares, so binding there makes "everything the world
holds is usable" true without a special case per producer.

Content stored *before* the environment has a bot needs one sweep: `Blueprint.build()`
materializes a declared forum topic through the same path `createForumTopic` takes, so its
`forum_topic_created` service message is in the chat before any `Bot` exists. `World.bind(bot)`
does that sweep once per environment, and the pruning of D3 makes it cheap.

### D3. An object that already has an owner is left alone, and the walk stops there

`mount` binds only *unbound* nodes and prunes the walk at bound ones. This is the ownership
rule, not a shortcut: because everything is bound the moment it enters the world, an object
that is already bound belongs to the environment.

It becomes load-bearing as soon as a **second** `Bot` shares the session — the documented
recipe for testing a codebase that sends through a module-level instance. Re-binding a stored
message to that second bot would silently change which `DefaultBotProperties` every later
shortcut on that message resolves against, and a `parse_mode` changing halfway through a test
is not a failure anyone would trace back here.

Pruning pays for itself twice: re-answering with a stored message stops at that message
instead of re-walking everything it transitively refers to.

*Consequence:* "whose is this" cannot be asked with `==`. `Bot.__eq__` compares token hashes,
so two environments built from one blueprint have equal — and therefore indistinguishable —
bots. `bound_elsewhere` compares identity.

### D4. A chat reads its owner off the world; the registry installs the backref

The first version stored a `bound_bot` on each `ChatState`, copied there when the environment
bound the world. It was wrong in the way copies are always wrong: a chat added *after* the
bind — the private chat that opens on demand, a chat a test drops in by hand — never got one,
and silently stored unbound messages.

`ChatState.bound_bot` is now derived: it reads `self.world.bound_bot`. There is exactly one
owner and one place holding it.

That needs every chat to know its world, and there is exactly one moment when a chat becomes
part of one: when it is put into `world.chats`. `ChatRegistry` does the wiring in
`__setitem__` — and, because `dict` implements `update`, `setdefault` and `|=` in C without
going through `__setitem__`, overrides those three as well. Overriding `__setitem__` alone
left three doors into the world that skipped the wiring, which is precisely the failure mode
the derived property was introduced to remove.

### D5. Copy *in* once, at `handle_call`

Eight handlers used to copy what they stored, and the ninth would have forgotten. The copy now
happens once, in `handle_call`, **after** the call log has recorded the caller's own object —
so `env.calls` still shows what the code under test actually built, while everything
downstream gets a `detached_copy`.

The rule a handler author now follows is "there is nothing to copy", which is a rule that
cannot be forgotten. It is stated in the module docstring of `aiogram/test/modeling.py`, where
the next handler is written.

### D6. Copy *out* the value objects; share the messages

The two directions are not symmetric, and the asymmetry is deliberate.

A `Message` the world stores is handed back **as it is**. `chat.messages[-1] is result` holds,
and an edit through either lands on both — that identity is a feature tests rely on.

Everything else the world stores is a *value* a test compares against a declared constant
(`chat.permissions == DECLARED`). A result gets mounted to the calling bot on the way out, so
handing out the stored instance would bind the world's own state — and leave that comparison
failing with two sides that print identically. `getChat`, `getMyCommands`,
`getMyDefaultAdministratorRights` and `getChatMenuButton` copy explicitly.

### D7. `detached_copy` rebuilds what it recognises and shares the rest

`copy.deepcopy` was tried and is unusable here: it follows a leaf's attributes, and one leaf
really does hold a bot — `URLInputFile(url, bot=...)` keeps one to stream through — so copying
leaves minted a twin of the bot, of its session, and of the whole environment and world behind
it. It also recurses once per level and gives up around 200 levels deep.

The copy is therefore assembled out of the three shapes a Bot API value is made of — pydantic
models, mappings and lists — plus the immutable containers a test may wrap them in. Everything
else is a leaf and is shared: a date, an enum, a sentinel, an uploaded `InputFile`. Nothing
here ever constructs an object it does not recognise, so nothing reachable through a leaf can
be duplicated — and a shared leaf carries no world state and no binding, which is why sharing
it is also correct.

Bindings are decided as the copy is made rather than by a second pass, because a model's
`_bot` lives in its private attributes, which the walk never follows. Passing `bot=` also lets
the answer path hand the session an already-owned object, whose `mount` then prunes at the
root instead of walking the graph again.

### D8. Updates are mounted before `feed_update`, and a foreign update is copied

`Dispatcher.feed_update` re-mounts an update carrying a different bot by dumping it to JSON and
validating it again. Arriving already mounted skips that round-trip, which is what makes
`received is chat.messages[-1]` true.

One walk tells the three cases apart. An update an actor built is this environment's and is
mounted in place. An update a test constructed by hand is unbound, and the same pass claims it.
An update carrying another environment's objects cannot be claimed at all — `mount` stops at
anything bound — so it is *copied*, and the copy is this environment's. Without that, a
module-level update fed to two environments would keep the first one's bot and every reply the
second one's handlers sent would land in the first one's world, silently.

A message an update carries is then registered in its destination chat. Normally there is
nothing to do — the actor put it there first and it is found by id and left alone. The case
this exists for is the copied update: without registering it the chat's allocator is behind, so
the bot's first reply is minted with the *same* `message_id` as the incoming message, and the
next edit hits whichever of the two `find_message` reaches first.

### D9. A declared override result is copied per call

The declared object belongs to the test and is often built once at module level; the answer
belongs to the caller, gets mounted to it, and may be edited by a modeled follow-up. Copying
per call makes a repeated override (`times=None`) behave like the API it stands in for, and
keeps a module-level constant from holding a reference to every `Bot` that ever received it,
long after those environments were disposed.

### D10. The plugin explains a binding-only inequality

The bot an object carries is part of its identity for pydantic, and the repr hides it — so an
object the fake hands out never compares equal to an identical one built inside the test, while
the two print identically. That is production behaviour, not a toolkit quirk, but it costs a
debugging session the first time.

`pytest_assertrepr_compare` detects same type, same dump, different bot and says so, pointing
at `model_dump()` as the comparison that works. The dump is guarded by a bare `except`, because
this hook runs on **every** failing `==` in every project that installs aiogram: pydantic-core
gives up on a deep graph, and an explanation that raises would replace the user's real
assertion failure with its own traceback. A comparison it cannot explain is one it declines to
explain.

## Risks / Trade-offs

- **The walk runs on every call and every trigger** → mitigated by pruning at owned objects
  (D3), by a single pass in `feed` that both asks whose the update is and claims it, and by
  minting override and derived copies already bound so the session's `mount` prunes at the root.
- **`derive_message` shares the untouched subtree with the original** → an edit only copies the
  *changes*. Detaching the whole derived copy, as it first did, walked that shared subtree and
  unbound the **original's** children, so a message the chat still held lost its shortcuts as a
  side effect of something else being edited.
- **Two objects that print identically are unequal** → real, shared with production, and now
  explained on failure (D10). The world's *stored* state is unbound, so assertions against
  declared constants still work there.
- **A handler could still capture the caller's object by reading it before the copy** → it
  cannot: the copy happens before any handler is reached (D5), and a test asserts that an
  unguarded handler storing a value straight off the method stores a copy.

## Migration Plan

Additive at the API level; behavioural where it matters. Shortcuts that previously raised now
work, and objects that previously compared equal to a test's constant may no longer, because
one side is now mounted. Both are called out in the changelog and the documentation.

## Open Questions

- Should `bindables` be public? It is exported from `aiogram.test.mounting` but not from
  `aiogram.test`, on the grounds that a test should never need to bind anything by hand. If a
  user does, that is a missing choke point, and the fix belongs here rather than in their
  conftest.
