## Context

Wave 4 shipped targeted overrides, routing diagnostics, broadcast waits, membership service
messages, promote/demote sugar and background-task draining — all against single-update,
single-recipient scenarios. An internal review round replayed each feature against the
scenarios wave 4's own field report had already surfaced elsewhere in the toolkit —
multi-update triggers, multi-field addressing, fixture-scoped background tasks — and found
ten confirmed gaps, each with a runnable repro. Findings are labeled `R1`–`R10` for
reference from the decisions below.

- **R1** — `member.join()` in a group feeds two updates (`chat_member`, then
  `new_chat_members`), but `last_route`/`assert_handled_by` only ever looked at the single
  most recently completed record. A bot that handled the `chat_member` transition and
  correctly ignored the service message failed `assert_handled_by("on_user_joined")` anyway,
  because the service message — nobody's handler — was the last thing routed.
- **R2** — Even once `assert_handled_by` could see more than one record, it needed to *scan*
  all of them rather than compare against a single "the" record, and a failure needed to
  dump every one of them, not just the last, to stay useful for a multi-update trigger.
- **R3** — `env.blocked(...)` only reached `DELIVERY_METHODS`. A bot whose failed-send
  recovery path edits its previous message, unpins it, or clears a reaction sailed straight
  through a block that only knew about `Send*`/`Copy*`/`Forward*`, so a test of that recovery
  path passed while proving nothing a real blocked user's bot would experience.
- **R4** — `sendGift` addresses its recipient by `user_id`, not `chat_id`. `env.blocked(...)`
  registered rules keyed on `chat_id` alone, so a gift to a blocked user sailed through
  unblocked, and the toolkit had no way to express "this user cannot receive gifts either."
- **R5** — `MethodMatcher.matches` compared addressing fields by plain equality. A bot that
  reads its config as `@username` and a test that names the same chat by numeric id compared
  `'@alice' != 1` and silently never matched — an override or a block declared for one
  spelling was invisibly absent for a bot using the other.
- **R6** — Nothing told a test that a declared override never fired. A one-digit-off chat id
  in a field filter registered cleanly, matched nothing, and the bot behaved as though the
  override were never declared — the failure then read as "the bot sent the message it was
  supposed to fail to send," far from the actual mistake.
- **R7** — `World.__setattr__`'s foreign-registry guard was the *only* place ownership was
  checked, and its own error message recommended the exact bypass that defeated it:
  `world.chats = dict(other.chats)` unwraps the live registry into a plain mapping, passes
  the `isinstance` check, and then goes through `ChatRegistry.__setitem__` one item at a
  time — which did no ownership check of its own — silently rewriting `chat.world` on
  objects the donor world still held.
- **R8** — `promote(**rights)` accepted any keyword at all. A misspelled
  `promote(can_pin_message=True)` (missing the trailing `s`) was silently dropped rather than
  granting anything, and the test failed later on the bot's own "you are missing a right"
  branch with no indication which right or why.
- **R9** — `promote`'s rights lived in `**kwargs` while `demote`'s dispatcher data lived in
  `**kwargs` too — the same keyword position meant two different things on the two triggers,
  a trap for exactly the kind of one-line change (`promote(..., data=...)`) a test reaching
  for both would make.
- **R10** — `drain()`'s protected-task snapshot was taken once, at construction. The
  `bot_env` fixture is synchronous, so an environment is normally built with no event loop
  running and that snapshot is empty; the first test in a session to call `drain()` then
  cancelled a session-scoped async fixture's own background worker, breaking every later
  test in the session. Separately, a task that failed on its own accord during drain was
  either swallowed or reported identically to a task that merely failed to finish in time,
  losing the real traceback either way.

## Goals / Non-Goals

**Goals:**

- Make routing diagnostics correct for a trigger that produces more than one update, not
  only for the single-update case.
- Make `blocked()` cover what a real block actually stops, addressed however a call happens
  to address it.
- Make a never-fired override diagnosable instead of silently absent.
- Close the registry-ownership hole at the layer that actually mutates the registry, not
  only at the layer that replaces it wholesale.
- Validate `promote()`'s rights the same way `env.on(...)`'s field filters are validated.
- Make `drain()` safe for a session-scoped async fixture regardless of when the environment
  happened to observe it running.

**Non-Goals:**

- Redesigning the trigger vocabulary itself; `trigger()` composes with every existing actor
  method rather than replacing any of them.
- A general capability-based rights model; `_validate_rights` only rejects unknown field
  names, exactly as `_validated_fields` already does for override filters.
- Solving loop-scoped-cache hazards from `drain()`; that remains explicitly out of scope, as
  wave 4 already decided.

## Decisions

### D1. A `ContextVar` carries "the record in flight," not a stack on the environment

Resolves R1/R2. The record a `_HandlerMiddleware` should fill in is a property of the
**task** routing an update, not of the environment: two updates fed concurrently
(`asyncio.gather(alice.send(...), bob.send(...))`) run in their own tasks, and a shared
stack on the environment let the inner middleware read whichever record happened to be on
top — a handler's name landing on the *other* update's record. A `contextvars.ContextVar` is
copied when a task is created, so concurrent feeds are isolated by construction, while a
nested feed (a handler feeding an update of its own, from inside the same task) still shadows
correctly and is restored by token. The variable is module-level rather than per-environment,
deliberately: `copy.deepcopy(world)` — which the toolkit's own blueprint machinery does —
would otherwise have to copy a `ContextVar`, which cannot be copied at all, and a shared
variable is simply correct here since what it holds is the innermost record of whichever
environment opened it.

### D2. `last_route`/`routes`/`assert_handled_by` reason about a trigger **scope**, not a single update

Resolves R1/R2. Every update fed inside one scope — directly, or through a multi-update actor
trigger like `join()` — belongs to that scope. A bare `feed` outside any explicit `trigger()`
block, and not itself nested inside one already open, opens a scope of its own, which is what
keeps the common one-update case free of ceremony. `routes` exposes every record of the scope
in completion order. `assert_handled_by` scans **every** record of the scope rather than only
the most relevant one, and its failure dumps all of them, including any captured exception —
the fix R2 asked for once R1's records were actually reachable.

**A scope is a context-local object keyed to an environment, not a counter and a list on the
environment.** The first implementation was `_trigger_routes` plus a `_trigger_depth` counter,
with "are we nested?" answered by reading the module-level `_ROUTE_IN_FLIGHT` from D1 — and
that was wrong three times over, each reproducible:

- `asyncio.gather` of two feeds that never suspend erased the first one's record, because the
  second feed's prologue cleared the one shared list;
- a feed running concurrently with, but unrelated to, an open `trigger()` block was absorbed
  into it, because the depth counter said "inside a trigger" for the whole environment rather
  than for the task that opened one;
- and the nesting flag was not even per environment — it was "some record is in flight,
  anywhere" — so an update fed to environment B *from a handler of environment A* looked
  nested to B and appended to whatever B had recorded minutes earlier.

So the open scope is a `_TriggerFrame` — a record list plus the environment it belongs to,
plus a `closed` flag — held in a `_TRIGGER_SCOPES` context variable (a tuple, innermost last).
`trigger()` pushes a frame if this environment has none open *in this context* and reuses the
outer one otherwise, which is how nesting keeps working; `feed` does the same; closing a frame
marks it closed, resets the token and publishes it as the environment's last completed
trigger. Records append to the innermost open frame of their own environment. A task copies
the context when it is created, so concurrent triggers get frames of their own by
construction, and the `closed` flag covers the copied context a background task keeps after
the block that created it ended — an update fed from there starts a fresh scope rather than
appending to a finished one. `routes`/`last_route`/`assert_handled_by` read the frame open in
this context if there is one, else the last completed frame; under `gather` that means "the
trigger that completed last," and a concurrent test asserts per branch by giving each branch a
`trigger()` block of its own. A record completing with no frame at all — `dispatcher.feed_update`
called directly, bypassing `feed` — becomes a finished one-record scope rather than being
dropped.

**`last_route` prefers the record that raised.** The order is: newest record carrying an
exception, else newest handled, else newest of any kind. The middle tier alone was wrong for
the case the diagnostic exists for: aiogram's error middleware sits outside anything an
environment can install, so a handler that raises leaves its record "not handled" with the
exception attached, while the trigger's *other* update is handled normally — and
`assert env.last_route.handled, env.last_route.describe()`, the idiom the docs recommend,
passed while the bot was on fire. The remaining two tiers are unchanged: `member.join()` still
reports the `chat_member` update its handler claimed rather than the `new_chat_members` service
message nobody wanted, and a scope nothing reacted to still reports "NOT handled".

Rejected: keeping a full session-long log of every route ever recorded. The diagnostic this
closes is "what did *this* trigger do," which a scope answers directly; a full log adds a
memory-growth question and a query API nothing has asked for.

Rejected: locking, or making concurrent triggers merge into one scope. Merging is what the
depth counter accidentally did, and it is the failure — two branches of a `gather` are two
things the test did, not one.

### D3. `BLOCKED_METHODS` extends `DELIVERY_METHODS` with a reviewed, explicit, exclusion-documented list

Resolves R3/R4. `BLOCKED_METHODS` is `DELIVERY_METHODS` plus a hand-listed tuple of the
`editMessage*` family, `stopMessageLiveLocation`, `stopPoll`, the **whole reaction family**
(`setMessageReaction`, `deleteMessageReaction`, `deleteAllMessageReactions`) and the
pin/unpin trio — every one of them an operation the bot performs *inside* a chat it must
still be able to reach, which a real block also refuses. The reaction family belongs in the
list together: covering only the setter let "clear the reaction I put on my own message", a
perfectly ordinary recovery path, pass a test its users never pass — the same gap the edit and
pin families were added to close. `deleteMessage`/`deleteMessages` are
a **documented exclusion**, not an oversight: the Bot API states their limits in terms of
message age and administrator rights, not of reachability, so a bot dropping its own
leftovers is not delivering anything, and guessing a 403 there would fail a cleanup path in
tests that succeeds in production — the more expensive of the two possible mistakes.

**The converse is written down as a maintenance rule**, because the list is only as good as
the next Bot API bump leaves it: a new `Send*`/`Copy*`/`Forward*` method joins by prefix on
its own, while a new `Edit*`/`Stop*`/`Pin*`/reaction method needs a row added here — or a line
in the exclusions saying why it stays out. Both halves are the review surface, which is why
the exclusions are written rather than left as the absence of a row.

`block_chat` registers one rule per `BLOCKED_METHODS` entry **per addressing field that names
the addressee** rather than one predicate trying to cover both, which keeps
`MethodMatcher.describe()` readable for a failure message and costs nothing at match time,
since a rule whose field the call lacks is walked past without being consumed. `chat_id`
always qualifies; `user_id` qualifies **only on a delivery method**, which is what makes
`sendGift`, addressed by `user_id` alone, block correctly. On the hand-listed extras `user_id`
names a *participant* of a chat the call addresses by `chat_id` — `deleteMessageReaction` takes
both — so keying on it would have blocked "clear the blocked user's reaction in a group", a
call a real block never touches, proving a failure production never sees.

Rejected: a single predicate matching "any of `chat_id`/`user_id` equals the blocked party."
A predicate cannot describe itself the way a field-equality matcher can, and
`assert_overrides_consumed`'s failure message (D5) depends on every rule being describable.

### D4. Chat-addressing fields are resolved symmetrically through the world before comparison

Resolves R5. `MethodMatcher.matches` takes an optional resolver; when given one (the
environment always supplies `resolve_addressing`), it tries exact equality first — which
costs nothing and handles the common case — and only on a mismatch resolves *both* the
matcher's declared value and the call's actual value through the world before comparing
again. `ADDRESSING_FIELDS` (`chat_id`, `from_chat_id`, `sender_chat_id`) is the fixed set of
fields this applies to; every other field stays exact, since equality is what
`env.on(Method, field=value)` promises. Symmetry is deliberate and tested in both directions:
a rule declared by numeric id catches a call addressed by `@username`, and a rule declared by
`@username` catches a call addressed by numeric id — either one alone would have left the
toolkit's own fix half-finished.

### D5. A rule's `fired` count is the ground truth for "did this override ever do anything"

Resolves R6. `OverrideRule` gains a `fired` counter, incremented by `OverrideRegistry.take`
exactly when a rule's matcher accepts a call — which is also the only place a rule's `times`
budget is spent, so a rule that leaves the registry by exhausting its budget necessarily has
`fired > 0`. `unfired()` is therefore simply "rules still registered with `fired == 0`," and
`assert_overrides_consumed()` raises naming them via `describe_unfired()`, the same
`MethodMatcher.describe()` rendering `assert_overrides_consumed` and a wait's own timeout
footer both reuse — one function, every diagnostic surface, so the two error messages stay
consistent by construction rather than by coincidence.

**But a rule is only reportable if it was an expectation**, which is the second half of this
decision and the one the first pass missed. `env.on(SendMessage, chat_id=alice.id).raises()`
is one expectation spelled as one rule. `env.blocked(alice)` is one *simulation* spelled as
forty-odd rules — one per method a block stops, per addressing field — of which the bot is
supposed to take one or two and leave the rest untouched. Counting each of those as a
never-matched declaration made both surfaces useless in exactly the block the documentation
recommends them for: `assert_overrides_consumed()` could not pass inside
`with env.blocked(alice):` at all, and every wait timeout in that block ended in a forty-line
wall about methods nobody expected to be called, burying the actual diagnosis.

So `OverrideRule` gains `expected: bool`, set where the *shape* of the declaration is known:
`OverrideHandle.register(..., expected=False)` for the rules a simulation generates,
defaulting to `True` for everything a test writes by hand. `unfired()` filters on it, which
excludes a block's rules **entirely** — not "forgiven once one of them fired". A simulation is
not a prediction of which of its alternatives the bot will take, so a block that never fired
is not a finding either; that is the ordinary shape of "prove the bot never went there".

Rejected: comparing rule counts per handle, or treating a handle as fired if any of its rules
fired. Both are the same idea one layer too high — they would report a hand-written handle
that declared several rules of which only one matched, which *is* a finding.

Rejected: making this checked automatically at teardown. A test that declares a rule for a
path it does *not* expect to be taken is a perfectly good test — proving the bot never went
there — so consumption-checking has to stay something a test opts into, exactly as `drain()`
does for background tasks.

### D6. Registry ownership is enforced in `ChatRegistry.__setitem__`, not only in `World.__setattr__`

Resolves R7. `World.__setattr__`'s guard against a foreign **live** registry remains — it is
still the fastest rejection for the common `w2.chats = w1.chats` mistake — but the actual
ownership rule now lives one layer down, in `ChatRegistry.__setitem__` itself: a chat whose
`.world` already names a *different* world is refused there, whatever container it arrived
in. This is what closes the hole the old message pointed straight at: `dict(other.chats)`
unwraps the live registry into a plain mapping, which passes `__setattr__`'s `isinstance`
check and then flows through `update()` — implemented, like `setdefault` and `|=`, in terms
of `__setitem__` precisely so nothing can route around it — one chat at a time. The
recommendation in `__setattr__`'s own error message changes accordingly: it no longer
suggests `dict(other.chats)`, since that is refused for the same reason and one layer closer
to where the actual mutation happens.

**What both messages recommend instead is verified to run**, which the first pass was not.
`ChatRegistry.__setitem__` used to open with
`world.chats[id] = blueprint.build().chats[id]  # from the declaration` — and a chat straight
out of `build()` is owned by the world that built it, so the reader who followed the advice
landed on the same refusal, printed by the same line, with nothing saying what the missing
step was. `World.__setattr__`'s message, having correctly withdrawn `dict(other.chats)`,
was left recommending nothing runnable at all. So:

- the per-chat refusal spells out three remedies, each with its detach step shown —
  `copy.deepcopy(chat)` for an independent copy, `blueprint.build().chats[id]` for a fresh
  chat of the same shape, and `del donor.chats[id]` for moving this very object — with the
  message stating outright that *every* one of them needs `chat.world = None` before the
  registration, because a chat handed over undetached lands right back here;
- the whole-registry refusal points at building the world you want and using it whole
  (`world = blueprint.build()`) rather than transplanting chats between worlds at all, and,
  for the case where moving the objects really is meant, at detaching them in a loop first.

The tests do not paraphrase this advice: they parse the code blocks out of the raised message
and `exec` them, so a recommendation that stops working fails here rather than in somebody
else's suite.

Rejected: making `del`/`pop` on a registry detach the chat automatically, so
`world.chats[id] = donor.chats.pop(id)` would read as one line. It hides a `chat.world`
mutation inside a removal, and the explicit detach is the thing that says which of the three
remedies the reader meant.

A **fresh** chat — one whose `.world` is still `None` — is always adopted normally, and a
chat already wired to *this same* world is left alone by identity, so re-assigning a world's
own `chats` to itself, or re-registering a chat under the id it already holds, both stay
no-ops. `copy.deepcopy(world)` continues to work because it rebuilds the registry through
`__setitem__` on a *copy* of each chat — a chat with no `.world` yet — never through
`__setattr__` and never touching a foreign live registry at all.

Rejected: keeping `__setattr__`'s check as the only one and additionally hardening
`ChatRegistry.update`/`setdefault`/`__ior__` by hand. Those three already route through
`__setitem__`; duplicating the check in each would be exactly the kind of "three doors, one
of them forgotten" bug this registry's own docstring already warns about for the *binding*
concern it solves the same way.

### D7. `promote()`'s rights are validated exactly like `env.on(...)`'s field filters

Resolves R8. `_validate_rights` checks every keyword in `**rights` against
`ChatAdministratorRights.model_fields` and raises `TypeError` naming the unknown ones,
mirroring `aiogram.test.overrides._validated_fields`'s shape deliberately: the same mistake
— a keyword that can only ever be a typo — reads the same way wherever the toolkit meets it.
Rights themselves are read off a masked namespace built the usual way (`mask(...,
SimpleNamespace(**rights), coerce=True)`), so a right that *is* valid still behaves exactly
as before; only the misspelled case changes, from silent nothing to a loud, actionable error.

### D8. `promote`/`demote` both take dispatcher data through `data=`, freeing `**kwargs` for rights alone

Resolves R9. `promote(subject=None, *, data=None, **rights)` reserves `**kwargs` entirely for
rights, and `demote(subject=None, *, data=None)` — which has no rights to reserve space for —
takes the same `data=` keyword anyway, so the two triggers agree on this even though only one
of them strictly needs to. The alternative each trigger had before (`promote`'s `**kwargs`
doing double duty, `demote`'s `**data` catching everything) meant the same-looking call
(`promote(..., data=...)` vs `demote(..., **data)`) did different things depending on which
of the two a test happened to be calling, which is exactly the kind of asymmetry worth
removing rather than documenting.

### D9. The owner-guard on a trigger raises `WorldLookupError`, never `ApiRejection`

A trigger arranges the world directly; it never goes through the intercepted call path
`ApiRejection` exists to model a refusal on. Promoting or demoting the chat's owner through
`admin.in_(team).promote(subject=owner, ...)` is therefore a **setup** mistake — the trigger
asking for a state that cannot exist — and raises `WorldLookupError`, matching every other
"the world cannot honor this trigger" refusal in the toolkit. The wording stays identical to
`handle_promote`'s own `ApiRejection` message on the *call* path, so the two failures still
read alike even though their types, and what a test should do about them, differ: a
`WorldLookupError` here says "fix the test's arrangement," while an `ApiRejection` on the
call path says "the bot's own `except` branch is what should run instead."

### D10. `drain()`'s protection is extended at this environment's first asynchronous action, and a task's own failure is never swallowed

Resolves R10. The task snapshot `drain()` subtracts is taken twice: once at construction
(covering the ordinary case, where a loop is already running), and again — unconditionally
extended, not replaced — at this environment's first asynchronous door, `feed` or
`handle_call`, whichever comes first. That second snapshot is the one that matters in
practice: `bot_env` is a synchronous fixture, so an environment is normally built with no
loop running at all and the construction-time snapshot is empty. Extending it again at the
earliest point a loop is guaranteed to exist, and still before the bot under test can
plausibly have spawned anything of its own, is what spares a session-scoped fixture's own
background worker without this environment ever having to know that fixture exists. A task
that ends with anything other than the `CancelledError` `drain()` sent it — a real bug in the
task itself — is collected and re-raised as `DrainedTaskError`, naming every such task with
the first one's traceback chained as `__cause__`, rather than being retrieved-and-discarded
(which would only stop asyncio's own "exception never retrieved" noise while hiding the bug
that noise was pointing at) or conflated with a task that is merely still running after its
cancellation, which stays a `WaitTimeoutError` — a different bug, a different exception.

Three gaps in that first pass are closed here:

- **A task that already died is inspected too.** `asyncio.all_tasks()` answers with the
  *unfinished* tasks only, so a night timer that raised three lines into the test was simply
  not in the set `drain()` looked at: it reported "0 tasks" and the `KeyError` surfaced, if at
  all, as a stray "Task exception was never retrieved" at collection time, attributed to no
  test. The only place asyncio records a task at all is its creation, so the environment wraps
  the loop's **task factory** at the same first asynchronous door, remembers every task made
  while it is live, and inspects the finished ones exactly as it inspects the cancelled ones.
  They are not cancelled (they are over) and do not count towards the returned number, which
  stays "how many tasks this drained". The wrapper delegates to any previous factory, so an
  eager or framework factory stays in force, and it is removed by identity at `_restore` — an
  environment whose factory is no longer the loop's leaves it alone rather than tearing a
  second environment's out from under it. References are strong until `_restore`, since a
  failed task collected before the drain takes its exception with it, which is the noise
  being prevented.
- **`drain()` on an environment that never ran does nothing.** With no snapshot at
  construction (the synchronous `bot_env` fixture) *and* no asynchronous entry since, "every
  unprotected task" means every task in the loop — so the first `await bot_env.drain()` of a
  test that only set things up would have cancelled the session-scoped fixtures' workers, the
  exact accident this protection exists to prevent. The environment owns nothing, so it
  cancels nothing and answers `0`.
- **A stuck task and a failed one, together, chain properly.** The stuck task stays the raised
  error, being the more structural failure, and the failure is named in its message as before
  — but the `raise ... from failures[0]` moves onto that `WaitTimeoutError` instead of being
  lost with the `DrainedTaskError` that is no longer raised. One `raise ... from` either way:
  whichever error comes out carries the first real failure's traceback.

Rejected: extending the protection on every `feed`/`handle_call` rather than once. The gap is
specifically about the moment *before* a loop can be observed running; once it has been
observed once, every task alive at that instant is already covered, and re-snapshotting on
every call would risk protecting a task the bot itself spawned later, defeating the point of
`drain()` in the first place.

Rejected: replacing the protection heuristic with the task factory's own record of "tasks
created after this environment's first asynchronous action". It would be more exact, but it is
a larger behavioral change than the reported gap asks for; the factory is used here only to
*observe*, never to decide what gets cancelled.

### D11. A user is part of the watch vocabulary, standing for their private chat

`as_views` — the one resolver behind `wait_for(watch=...)` and `wait_for_message_in(chats=...)`
— accepted chat and topic declarations, live states and bare ids, but not a `UserSpec` or a
`UserState`. The broadcast the whole family exists for is "every player got the night
keyboard", and what a test holds for a player is the declaration `add_user` handed back: the
example in `wait_for_message_in`'s own docstring is literally `wait_for_message_in(players, ...)`,
and passing that list raised `WorldLookupError` from inside the resolver. So a user is in the
vocabulary, resolved through `BotTestEnvironment.chat`, which means the private chat is *opened*
if the blueprint never declared one — the same rule `env.user(alice).chat` already follows, and
the same accessor, so the two cannot drift. None of the six accepted types is iterable, so
accepting a lone item alongside iterables still cannot guess wrong.

## Testing

- `test_route_diagnostics.py::TestTriggerScope`: a `join()` in a group reports the handler
  that claimed the `chat_member` transition even though the `new_chat_members` service
  message went unclaimed; either update's handler is found; `routes` holds both records of
  the scope.
- `test_overrides.py::TestBlockedCoversMoreThanDelivery`: editing, pinning and reacting in a
  blocked chat all fail; `sendGift` addressed by `user_id` is blocked; deleting is
  deliberately unaffected; an unrelated chat is untouched by any of it;
  `TestUsernameAddressing`: a block by id catches a call by username and vice versa,
  including the leading-`@` being optional on either side, another chat's username is not
  caught, and an unresolvable username matches nothing; `TestNeverMatchedOverridesAreNamed`:
  the assertion, a wait timeout and a broadcast-wait timeout all name a never-fired override,
  a fired or cancelled one is not named, and a predicate rule describes itself by name.
- `test_world.py`: assigning another world's live registry is refused; unwrapping it into
  `dict(other.chats)` does not get past the refusal; a detached chat can be moved; a fresh
  chat is adopted normally; re-registering a chat in its own world is a no-op; a deep copy of
  a world keeps its chats wired to the copy.
- `test_membership_triggers.py`: a misspelled right raises `TypeError` naming the valid
  ones; `data=` reaches the handler on both `promote` and `demote`; the owner guard raises
  `WorldLookupError` on both directions.
- `test_environment.py`: a task alive at the first `feed` is spared even though the
  construction-time snapshot was empty; a call also extends the protection; a task that
  fails of its own accord, or while being cancelled, surfaces as `DrainedTaskError` with its
  traceback chained; a stuck task is still reported as `WaitTimeoutError`, together with any
  failed task found alongside it.
