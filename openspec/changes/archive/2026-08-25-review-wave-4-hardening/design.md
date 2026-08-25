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

Resolves R1/R2. `BotTestEnvironment.trigger()` is a re-entrant context manager: entering it
at depth zero clears the scope's record list, and every update fed inside it — directly, or
through a multi-update actor trigger like `join()` — appends to that same list. A bare `feed`
outside any explicit `trigger()` block, and not itself nested inside a handler already
routing an update, opens a scope of its own, which is what keeps the common one-update case
free of ceremony. `routes` exposes every record of the current scope in completion order.
`last_route` is the **newest handled** record among them, falling back to the newest record
of any kind only when nothing in the scope was handled — the ordering that makes
`member.join()` report the `chat_member` update its handler claimed rather than the
`new_chat_members` service message nobody wanted, while a scope nothing reacted to still
reports "NOT handled" instead of hiding behind an earlier, unrelated success.
`assert_handled_by` scans **every** record of the scope rather than only the most relevant
one, and its failure dumps all of them, including any captured exception — the fix R2 asked
for once R1's records were actually reachable.

Rejected: keeping a full session-long log of every route ever recorded. The diagnostic this
closes is "what did *this* trigger do," which a scope answers directly; a full log adds a
memory-growth question and a query API nothing has asked for.

### D3. `BLOCKED_METHODS` extends `DELIVERY_METHODS` with a reviewed, explicit, exclusion-documented list

Resolves R3/R4. `BLOCKED_METHODS` is `DELIVERY_METHODS` plus a hand-listed tuple of the
`editMessage*` family, `stopMessageLiveLocation`, `stopPoll`, `setMessageReaction` and the
pin/unpin trio — every one of them an operation the bot performs *inside* a chat it must
still be able to reach, which a real block also refuses. `deleteMessage`/`deleteMessages` are
a **documented exclusion**, not an oversight: the Bot API states their limits in terms of
message age and administrator rights, not of reachability, so a bot dropping its own
leftovers is not delivering anything, and guessing a 403 there would fail a cleanup path in
tests that succeeds in production — the more expensive of the two possible mistakes.
`block_chat` registers one rule per `BLOCKED_METHODS` entry **per addressing field it
actually has** — `chat_id` and, where present, `user_id` — rather than one predicate trying
to cover both, which keeps `MethodMatcher.describe()` readable for a failure message and
costs nothing at match time, since a rule whose field the call lacks is walked past without
being consumed. This is what makes `sendGift`, addressed by `user_id` alone, block correctly.

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
to where the actual mutation happens; it instead points at detaching a chat explicitly
(`chat.world = None`) before re-registering it, or building the chats a world needs from
their declaration.

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

Rejected: extending the protection on every `feed`/`handle_call` rather than once. The gap is
specifically about the moment *before* a loop can be observed running; once it has been
observed once, every task alive at that instant is already covered, and re-snapshotting on
every call would risk protecting a task the bot itself spawned later, defeating the point of
`drain()` in the first place.

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
