## Why

Waves 2 and 3 hardened the toolkit against edge cases probed directly — foreign objects,
foreign registries, id collisions. Wave 4's field report comes from a different kind of
use: real bots exercised through real test suites, where the pain is not an edge case but
the shape of an everyday scenario the toolkit did not yet have words for.

- A bot that reacts to one trigger by messaging several chats — a game engine telling the
  group and every player at once — cannot be told "this one player blocked the bot."
  `env.on(SendMessage).raises(times=1)` answers whichever call happens to come first,
  so testing two blocked players at once was not expressible, and testing one meant either
  reordering production code or accepting a flaky assertion.
- An update that dies in a middleware, or lands in a catch-all logging handler instead of
  the handler under test, comes back from a trigger looking exactly like one that reached
  its intended handler — both are "the trigger returned a value." The test only learns
  something went wrong minutes later, from an unrelated `wait_for` timing out with nothing
  to say about why.
- `wait_for` reports the condition it was given, but the condition is a lambda over the
  bot's own state, and the useful diagnostic — what the bot posted *instead* — was not
  available without a second, manual read of the chat. A bot that fans one event out to
  many chats had no single wait at all: testing it meant awaiting each chat's own
  `wait_for_message` in series, which is slower and fails by naming only the first chat
  that missed its message, hiding a systematic failure behind what looks like one unlucky
  recipient.
- `join()` / `add_bot()` produce only the membership update, never the `new_chat_members`
  service message a real join or add also delivers in a group. A "welcome new members"
  handler — one of the most common handlers a group bot has — was untestable by trigger
  alone.
- There was no actor-level sugar for promotion (`promote()`/`demote()`), for replying
  (`send(reply_to=...)`, `reply()`), and a misdirected `click()` — a forgotten `.in_(chat)`
  — read identically to a genuine typo in `callback_data`, the two failure modes
  indistinguishable without independently checking every chat by hand.
- `env.chat(user_id)` raised for a declared user whose private chat the blueprint did not
  separately declare, while `env.user(user).chat` already opened it on demand for the exact
  same id — the same chat reachable through one accessor and not the other.
- A bot with an engine of its own leaves tasks running past the end of a test. Nothing in
  the toolkit could clean them up, so a project either accepted the stderr noise of
  destroyed pending tasks or hand-rolled its own cancellation in every affected test.
- Wave 3's registry guard (`world.chats = ...`) fixed the case where the assigned value was
  a plain mapping, and separately fixed `w2.chats = w1.chats` by *rewrapping* the foreign
  registry into one wired to `w2`. Continued field use surfaced that the rewrap itself is
  the wrong fix: a registry holds the donor's own `ChatState` objects, not copies, so
  installing it here rewrites `chat.world` on objects `w1` still holds — silently binding
  `w1`'s own chats, and everything they store afterwards, to `w2`'s bot. The fix that closed
  one bug quietly became a second, worse one.

## What Changes

- **Overrides can be targeted.** `env.on(Method, **fields)` narrows a rule to calls whose
  resolved fields equal the given values, ANDed, and `.where(predicate)` narrows further by
  anything a field equality cannot say. Several rules for one method are tried oldest
  first, and a rule whose shape rejects a call is skipped without spending its `times`
  budget — the property that makes two independently-blocked recipients expressible at
  all. `env.on(...)` now also returns a handle: `.cancel()` withdraws exactly what that
  call registered, and the handle works as a context manager. `env.blocked(chat_id=...)`
  is the named recipe for "this recipient's bot is unreachable," covering every method
  that delivers into a chat rather than only `sendMessage`, carrying no `times` budget of
  its own. The call log still records a call before any override — including `blocked` —
  answers it, so a test can assert both halves of a refusal.
- **Routing is inspectable.** `env.last_route` reports whether the most recently fed update
  was handled, by which handler and router, and the first exception raised in the
  middleware chain or the handler — captured where it was raised even when a bot's own
  error handler swallows it. `env.assert_handled_by(name)` is the assertion spelled
  directly, failing with a description of where the update actually went.
- **Waits gained a diagnostic and a broadcast form.** `wait_for(..., watch=chat)` appends
  one chat or topic's contents — or several — to the timeout message. New
  `wait_for_message_in(chats, predicate)` polls several chats together and returns once
  every one of them holds a match, failing by naming only the chats still missing one.
- **`join()`/`add_bot()` post the group's own announcement.** In a group or supergroup,
  both now also feed the `new_chat_members` service message a real join or add delivers
  alongside the membership update, after it — suppressible per call with
  `service_message=False`. A private chat, which has no such concept, never gets one.
- **New actor sugar.** `promote()`/`demote()` grant or clear administrator status,
  defaulting to the bot itself and refusing the chat's owner exactly as
  `promoteChatMember` does. `send(reply_to=...)` and `reply()` set `reply_to_message`
  directly. A `click()` that cannot find its button in the actor's own chat, but finds one
  with the same `callback_data` elsewhere in the world, names that chat instead of failing
  identically to a genuine typo.
- **`env.chat(user_id)` agrees with the actor path.** A bare id naming a declared user
  whose private chat was not separately declared now opens it, the same as
  `env.user(user).chat` already does for that id.
- **Background tasks can be drained.** `await env.drain(timeout=...)` cancels and awaits
  every task the test itself spawned and reports how many there were. It is opt-in, not
  wired into `dispose`/`dispose_sync`.
- **Assigning another world's live chat registry now raises**, replacing wave 3's rewrap.
  `w2.chats = w1.chats` is refused, naming the ownership rule, and `w1`'s own chats are
  left exactly as they were. Sharing chat objects across worlds is still possible, stated
  explicitly: `w2.chats = dict(w1.chats)`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: overrides gain field/predicate targeting, a cancellable
  handle, and the `blocked()` recipe; the private-chat-on-demand requirement extends to the
  environment's own chat accessor; the chat-registry requirement's foreign-assignment case
  now raises instead of rewrapping; waits gain `watch=` and the new broadcast requirement;
  two new requirements cover routing diagnostics and draining background tasks; the
  membership, promotion and reply/click requirements gain their own new entries.

## Impact

- **Code**: `overrides.py` (`MethodMatcher`, `OverrideRule`, `OverrideRegistry`,
  `OverrideHandle`, `OverrideBuilder`, `block_chat`, `DELIVERY_METHODS`); `environment.py`
  (`RouteRecord`, the routing middlewares, `last_route`, `assert_handled_by`, `wait_for`'s
  `watch=`, `wait_for_message_in`, `drain`, `chat()`'s widened resolution,
  `handle_call`'s call-log-before-override ordering); `world.py` (`World.__setattr__`'s
  registry guard now raising on a foreign live registry); `actors.py` (`promote`, `demote`,
  `send`'s `reply_to`, `reply`, `join`/`add_bot`'s `service_message` and the
  `new_chat_members` message, the click misdirection hint).
- **Tests**: `test_overrides.py` (targeting, handles, `blocked`), `test_route_diagnostics.py`
  (new), `test_waiting.py` (`watch=`, `wait_for_message_in`), `test_membership_triggers.py`
  (new — service message, promote/demote, owner guard), `test_reply_sugar_and_click_hints.py`
  (new), `test_world.py` (registry assignment now raising), `test_environment.py` (`drain`,
  `chat()` widening).
- **Docs**: `docs/dispatcher/testing.rst` — overrides section gains targeting, the blocked
  recipe and the call-log-ordering note; a new routing diagnostics section; the waits
  section gains `watch=` and the broadcast wait; the joining/leaving narrative gains the
  service message and a promoting/demoting subsection; a new background-tasks-teardown
  section covers `drain()` and the loop-scoped-cache hazard; the private-chat section notes
  `env.chat`'s widened resolution.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry — the
  toolkit is unreleased, so there is no released behavior to describe a change to.
- **Risk**: the registry-assignment change is a hard behavioral flip — code that relied on
  wave 3's rewrap (`w2.chats = w1.chats` silently working) now sees `WorldLookupError`
  instead. That is the fix working as intended: the rewrap was itself a bug, discovered only
  by continued use, and the loud refusal is what closes it for good rather than trading it
  for a third, quieter failure mode.
