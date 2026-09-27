## Context

Waves 2 and 3 hardened the toolkit against edge cases found by probing it directly — a
foreign object, a foreign registry, an id collision. Wave 4's field report is different in
kind: it comes from running real bots through real test suites, and every finding below is
a scenario the toolkit had no vocabulary for, not a bug in a scenario it already covered.
Findings are labeled `W4a`–`W4h` for reference from the decisions below.

- **W4a** — Wave 3's registry guard rewraps a foreign live registry
  (`w2.chats = w1.chats` installs a registry wired to `w2`). Continued use turned up why
  that is itself wrong: a registry holds the donor's own `ChatState` objects, and
  registering them under `w2` rewrites `chat.world` on objects `w1` still holds — so `w1`
  silently starts binding messages to `w2`'s bot the next time it stores one. The rewrap
  traded a loud failure (an `isinstance` check that missed this case entirely) for a
  *quiet* one, which is worse: nothing tells the test anything went wrong until a much
  later assertion fails for an unrelated reason.
- **W4b** — A bot that messages several chats from one trigger cannot have "this one
  recipient blocked the bot" expressed. `env.on(SendMessage).raises(times=1)` answers
  whichever call happens to come first, so the test either reorders production code to put
  the interesting recipient first, or cannot express the scenario for two recipients at
  once at all.
- **W4c** — An update that dies in a middleware, or is claimed by a catch-all handler
  instead of the one under test, is indistinguishable from a handled trigger: both return a
  value from `feed`/the actor's own trigger call. Diagnosis happens only later, from an
  unrelated timeout.
- **W4d** — `wait_for`'s failure message can only describe the condition, a lambda over the
  bot's own state; what the bot posted instead — almost always the real answer to "why not"
  — required a second, separate read. A bot that fans one event out to many chats had no
  single wait to cover it: awaiting each chat's `wait_for_message` in series is slower and,
  worse, fails by naming only the first chat that missed its message.
- **W4e** — `join()`/`add_bot()` never produced the `new_chat_members` service message a
  real join or add also delivers in a **group or supergroup**. A "welcome new members"
  handler — filtering on that field — could not be triggered at all.
- **W4f** — No actor-level sugar existed for promotion, for replying, or for naming where a
  misdirected `click()`'s button actually lives; each was either hand-rolled per test or,
  for the click case, indistinguishable from a genuine typo.
- **W4g** — `env.chat(user_id)` raised for a declared user whose private chat was not
  itself declared, while `env.user(user).chat` already opened the same chat for the same
  id. The asymmetry meant a chat reachable through one accessor and not the other.
- **W4h** — Background tasks a bot's own engine spawns outlive the test that triggered
  them; nothing in the toolkit cleaned them up, so a project either accepted the resulting
  stderr noise or hand-rolled cancellation per affected test.

## Goals / Non-Goals

**Goals:**

- Make "this recipient's delivery fails, that one's does not" expressible without
  reordering production code.
- Make a routing mistake diagnosable from the update that caused it, not from a later,
  unrelated timeout.
- Close the remaining wait ergonomics gaps: a diagnostic dump and a broadcast form.
- Cover the join/promote/reply actor surface real group bots exercise constantly.
- Resolve the registry rewrap loudly rather than trading it for a third failure mode.
- Give background tasks an explicit, opt-in cleanup path.

**Non-Goals:**

- A general subscription/event-bus mechanism for routing diagnostics. `last_route`
  reports the *last* update only, on purpose — see D3.
- Automatic task draining on teardown. See D8; a test that wants its tasks gone says so.
- Solving the loop-scoped-cache hazard (a middleware's own resource outliving the test's
  event loop) inside the toolkit. `drain()` cancels tasks; a stale cached connection is not
  a task, and no amount of draining reaches it — the fix is in how a project builds such
  resources, and the documentation says so rather than the toolkit pretending to.

## Decisions

### D1. Override targeting is field equality plus predicate, evaluated on the resolved method

`env.on(Method, **fields)` stores the keyword arguments as a tuple of `(name, value)`
pairs on a frozen `MethodMatcher`, checked against the method *after* `resolve_defaults`
has filled in bot-level defaults — the same object the call log records — so a filter on
`parse_mode` matches a call that never stated it and inherited it from `Bot(default=...)`,
consistent with what the real API would have seen. `.where(predicate)` appends an arbitrary
callable to the same matcher for anything a field equality cannot say (a text substring, a
particular button). A field name the method does not have raises `TypeError` at
declaration time rather than registering a rule that can never match — the alternative is
the worst kind of silent failure, a typo'd filter that never fires, discovered only when
the test fails for the wrong reason much later.

Rejected: matching on the method as originally constructed by the handler, before defaults
are resolved. That would make a filter's truth depend on whether the handler happened to
state a field explicitly, which is not a distinction the real Bot API makes and not one a
test should have to track.

### D2. A rule that does not match is not consumed — `take` walks past it, unmodified

`OverrideRegistry.take` iterates rules in registration order and returns the outcome of the
first whose matcher accepts the call; a rule whose matcher rejects the call is left
untouched, including its `times` budget. This is the property W4b actually needs: two
`times=1` rules addressed to two different chat ids stay independent of the order the
engine happens to message those chats in, because a call to chat A never touches chat B's
rule at all. `env.blocked(chat_id=...)` is built from the same registry and the same
`take`, with no `times` budget of its own — a block holds for as long as it is registered,
not for a fixed call count, matching what a real block means.

### D3. `last_route` reports the *last* fed update, not a log of every one

A `RouteRecord` is opened by an outer middleware registered on the dispatcher's `update`
observer (inside aiogram's own error-handling middleware, which is what lets it see an
exception a bot's own error handler swallows) and closed when that middleware's `handler`
call returns; an inner middleware registered on every other observer fills in the winning
handler once filters have passed. `last_route` is cleared at the start of every `feed` and
set once, so it can never be mistaken for a previous update's record. Keeping a full log
was considered and rejected: the diagnostic this closes is "what happened to *this*
trigger's update," which a single most-recent record answers directly, while a log adds a
memory-growth question and a query API for a use case that has not come up. A project
wanting history can read `last_route` immediately after each trigger it cares about.

`handled` follows the dispatcher's own definition — anything other than `UNHANDLED` came
back — which a middleware that returns without calling the next one already satisfies; that
is why `handler` is a separate field rather than folded into `handled`. Distinguishing the
two is the whole point of W4c: "the update was handled" and "a handler actually ran" are
different questions, and conflating them is exactly what made a middleware-swallowed update
indistinguishable from a routed one.

### D4. `watch=` reuses the chat/topic's own `describe_messages()`; `wait_for_message_in` reuses `newest_match`

Both waits are additions on top of existing machinery rather than new state: `watch=`
accepts one `ChatState`/`TopicState` or an iterable of them and appends each one's own
`describe_messages()` rendering to the timeout message, the same rendering
`wait_for_message`'s own failure already uses — one function, two call sites, so the two
error messages read consistently by construction. `wait_for_message_in` polls every named
chat's messages through the same `newest_match` helper a single chat's `wait_for_message`
already uses, so "the newest match wins, by id" is one rule stated once rather than two
implementations that could drift. A timeout names only the chats still missing a match,
computed by re-running `newest_match` over each chat at failure time, which is what makes
the failure message answer "who didn't get it" instead of "which chat happened to be
checked first."

### D5. `new_chat_members` is scoped to a group or supergroup, and follows the membership update

Resolves W4e. The service message is only produced when
`chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}` — a private chat has no concept of
"adding" someone to it (a bot starting a DM is not what `join`/`add_bot` model at all), and
a channel's membership changes arrive only as `chat_member`/`my_chat_member` with no
matching service message in a real client either. This is a **narrower** scope than "every
chat with members," stated explicitly rather than left to fall out of whichever chat types
happen to have a `members` dict, because getting it wrong in the permissive direction would
have a private-chat test see a service message no real Telegram client ever shows it.

Ordering is membership-update-then-service-message, not the reverse, because that is the
order Telegram's own clients display the two events in: the membership transition is what
happened, the service message is the group's own announcement of it, so the announcement
follows. The trigger's return value stays the membership update's handler result either
way — the service message is fed but not awaited for its own result, consistent with how
every other update a trigger feeds only for its side effects is handled. `service_message`
defaults to `True` rather than requiring an opt-in, since the previous single-update
behavior was the gap being closed, not a case to keep as the default; `service_message=False`
is the escape hatch for a test that specifically wants the old shape.

### D6. Promotion/demotion sugar defaults its subject to the bot, mirroring `promote()`'s existing rights-mask rule

`promote(subject=None, **rights)` resolves `subject` to the bot itself when omitted — the
survey of what group bot tests actually do first is promoting the bot, not some other
member — and otherwise accepts anything `_resolve_member_subject` already normalizes
(`UserSpec`, `UserState`, or a bare id). The rights passed are the whole mask, exactly
mirroring `promoteChatMember`'s own "a right not named is denied" rule (see
`handle_promote`), but a bare `promote()` with no rights at all still promotes rather than
reading as a demotion: the raw API's "all `False` means demote" convention only makes sense
when the caller is forced to state every field, and nothing forces that here, so treating
an empty call as a demotion would make the sugar do the *opposite* of what it says.
`demote()` is the trigger that says "take the status away," clearing rights and the custom
title while leaving `tag` untouched — the same asymmetry `handle_promote` already documents
for the raw call, restated here rather than re-derived, so the two paths agree by
construction rather than by coincidence. Both refuse the chat's owner with the same
`ApiRejection("can't remove chat owner")` the raw call raises, checked directly in
`_guard_not_owner` rather than routed through the modeled call path, since a trigger acts
on the world's own state and is not itself a Bot API call to intercept.

### D7. The click misdirection hint scans the rest of the world only after the actor's own chat fails to find the button

`_find_button_message` still raises first; `_misdirected_callback_hint` is called only to
build the message of that raised error, and it walks every *other* chat's messages looking
for the same `callback_data` before giving up. This keeps the common, successful path free
of the extra walk — the hint is pure diagnostic overhead paid only on the failure path,
where cost no longer matters and clarity does. Finding the button in an unrelated chat
would be a false positive worse than no hint at all, so the scan is exhaustive (every chat,
every message) rather than heuristic.

### D8. `drain()` is opt-in and separate from `dispose`/`dispose_sync`; it does not address W4h's loop-scoped-cache cousin

Two reasons, and the first is structural: `dispose_sync` — what the pytest fixture's
teardown calls — cannot await anything, so an automatic drain would work through the async
`dispose()` path and silently not through the sync one, which is worse than no automatic
draining at all because it would work in some projects and not others for no reason a user
could see. The second is about surprise: cancelling tasks a test never mentioned, as an
invisible side effect of a fixture going out of scope, turns "my bot's scheduler stopped"
into a debugging session. A test that wants its tasks gone says so with `await env.drain()`.

`drain()` only reaches `asyncio.Task` objects created after the environment was built (a
snapshot taken at construction is subtracted from the live task set at drain time), and
explicitly does **not** address the loop-scoped-cache failure mode also seen in the field:
a package- or session-scoped dispatcher fixture whose middleware opens a loop-bound
resource (a Redis client in a `ThrottlingMiddleware`, most commonly) binds that resource to
whichever event loop was running the first time it ran, and every later test — each on its
own fresh loop under most async test runners — inherits a client bound to a *dead* loop.
That is not a task in flight; it is a cached handle, and no amount of task cancellation
touches it. The documentation names this directly as its own hazard with its own fix
(construct such resources per test, or use a loop-aware client) rather than implying
`drain()` is a general background-task solution that happens to fall short here.

### D9. The foreign-registry assignment is refused loudly, resolving W4a — not rewrapped a second time

Wave 3 already tried the quiet fix: convert `isinstance(value, ChatRegistry)` into
`isinstance(value, ChatRegistry) and value.world is self`, and rewrap anything that fails
either half into a fresh registry wired to `self`. That closed the case a plain `dict`
assignment already covered, but for a *foreign live registry* it is the wrong shape of fix
entirely — rewrapping does not copy the chats, it re-registers the donor's own `ChatState`
objects, which means `w2.chats = w1.chats` rewrites `chat.world` on objects `w1` is still
holding onto. `w1` itself never reassigned anything; it silently starts binding new
messages to `w2`'s bot the next time it stores one, discoverable only by an assertion far
downstream of the actual mistake, if at all.

`World.__setattr__`'s guard therefore splits into two cases with two different outcomes, not
one case with a graduated fix. A value that is not a `ChatRegistry` at all — the plain-`dict`
case wave 2 and 3 already handle — is still wrapped: `world.chats = {1: chat}` is the
obvious way to rebuild a world's chats in a test, and there is nothing foreign to protect
here, only unwired chats to wire. A value that **is** a live `ChatRegistry` belonging to a
*different* world is refused outright, raising `WorldLookupError` and leaving both worlds
exactly as they were — `w1`'s chats stay `w1`'s, `w2`'s assignment simply did not happen.
This is the "loud refusal" resolution of W4a: the donor world's data was never at risk to
begin with, because the operation that would have put it at risk no longer completes.

A registry already wired to `self` — `world.chats = world.chats` — is left alone by
identity, matching `test_a_registry_assigned_as_is_is_left_alone`'s existing expectation and
keeping `copy.deepcopy(world)` working (`__setitem__`, not `__setattr__`, drives the copy's
own registry construction, so the guard never sees a foreign registry there at all).

Rejected: keeping the wave-3 rewrap and only *warning* about it (a `stacklevel`-correct
`warnings.warn`). A warning is exactly what a test suite's own filters silence by default,
and W4a was found in a suite that had been running the rewrapped version for a while before
anyone noticed messages arriving in the wrong world — a warning would not have changed that
outcome. Rejected also: copying the chats automatically instead of refusing. Silently
choosing "copy" on the caller's behalf is still a guess about what the caller meant, and the
whole point of D9 is to stop guessing; `dict(other.chats)` states the same intent as one
explicit call, so the toolkit does not have to infer it.

## Testing

- `test_overrides.py`: two independently-`times=1`-blocked chat ids interleaved with an
  unrelated third recipient; a `.where` narrowing applied after an earlier declaration on
  the same builder does not retroactively narrow it; an unknown field raises at declaration
  time; a handle's `.cancel()` leaves other declared rules alone; `env.blocked` covers every
  `DELIVERY_METHODS` entry and leaves an unrelated chat unaffected; a call answered by a
  raising override is still present in the call log.
- `test_route_diagnostics.py`: a handled update names its handler and router; a
  middleware-swallowed update reports `handled=True` with `handler=None`; a catch-all
  handler is named rather than confused with a more specific one that did not match; an
  exception a bot's own error handler swallows is still captured on the record; the record
  resets between two fed updates; `assert_handled_by` fails naming the actual route,
  including a captured exception.
- `test_waiting.py`: `watch=` on a condition wait includes the named chat's rendering in a
  timeout; `wait_for_message_in` returns once every named chat has a match, accepts a mix
  of declaration/state/id, resolves the newest per-chat match, and names only the chats
  still missing one when it times out.
- `test_membership_triggers.py`: `add_bot()`/`join()` in a group post `new_chat_members`
  after the membership update, and the trigger's return value is unaffected by it;
  `service_message=False` suppresses it; a private chat never receives one regardless;
  `leave()`/`remove_bot()` are unaffected; `promote()`/`demote()` default to the bot,
  accept a named subject, grant/clear exactly the stated rights, keep the tag across a
  demotion, and both refuse the chat's owner.
- `test_reply_sugar_and_click_hints.py`: `send(reply_to=...)` and `reply()` set
  `reply_to_message` by object and by id, with an explicit `fields` override still winning;
  a misdirected `click()` names the chat that actually holds the button and does not fire
  when the button exists nowhere.
- `test_world.py`: `w2.chats = w1.chats` raises, naming the ownership rule, and leaves
  `w1`'s chats wired to `w1`; `w2.chats = dict(w1.chats)` still shares the chat objects
  while wiring them correctly to `w2`.
- `test_environment.py`: `env.chat(user_id)` opens a declared user's private chat rather
  than raising; `drain()` cancels and awaits a task created after the environment was
  built, leaves a pre-existing task alone, and raises if a task outlives its cancellation.
