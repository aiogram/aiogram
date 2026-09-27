## Context

Four of these five findings are the same shape: wave-2 drew a boundary correctly for the
case it was written against, and a slightly different case walks around it. The fifth is a
documentation correction from measured field data, not a code change.

## Goals / Non-Goals

**Goals:**

- Close the two remaining ways a chat can end up wired to the wrong world.
- Make a message-id collision from a carried update fail the test instead of the wait that
  depends on it.
- Remove the last piece of fixture-copying ergonomics the plugin still forced.
- Widen `ensure_private_chat` to the same three input forms the rest of the toolkit already
  standardized on.

**Non-Goals:**

- Re-litigating the registry-guard or carried-message designs wave-2 shipped. Both are
  extended in place, not redesigned.
- A general "accepts spec or id" helper. Each call site duck-types the same three-way split
  `BotTestEnvironment.user` already established; a shared helper would save a few lines at
  the cost of a name nobody would otherwise need to look up.

## Decisions

### D1. The registry guard checks `value.world is not self`, not just `isinstance`

`World.__setattr__` converted a `chats` assignment whenever the value was not already a
`ChatRegistry`. That covers a plain `dict` — the case the wave-2 regression test exercises —
but not a *different* world's registry, which already passes `isinstance`.

The fix adds one condition: `not isinstance(value, ChatRegistry) or value.world is not self`.
A registry belonging to `self` is left alone by identity (`world.chats = world.chats` stays a
no-op, matching the existing `test_a_registry_assigned_as_is_is_left_alone`); anything else —
a plain mapping, or a registry wired to a different `World` — gets a fresh `ChatRegistry(self)`
populated through `.update()`, which is what wires each chat's `.world` to `self`.

One consequence worth stating plainly, because it is easy to assume otherwise: chats are not
copied. `w2.chats = w1.chats` rewires the *existing* `ChatState` objects that came along —
`w1.chats[1] is w2.chats[1]` afterward, and that shared object's `.world` now names `w2`, not
`w1`. `w1`'s own chat registry object is untouched (`w1.chats[1] is w2.chats[1]` doesn't
change what `w1.chats` itself is wired to), so a chat added to `w1` afterward is still wired
to `w1` correctly — only the objects that were actually carried across move. This matches how
the wave-2 "replace the mapping with a plain dict" case already behaved; the fix is symmetric
across "the value is a foreign registry" and "the value is a plain mapping" rather than
introducing new semantics for the registry case.

### D2. The collision guard compares by equality, computed after binding

The naive fix — raise whenever `chat.find_message(id) is not None` — breaks the existing
no-op path: an update fed twice (`test_an_actor_built_update_is_fed_without_a_copy`) and the
two-environment recipe's own re-delivery both re-present a message under an id the chat
already has, and neither is a bug.

`_register_carried_message` runs after `feed()`'s own binding step, so by the time it sees the
incoming message, that message is already bound to *this* environment's bot — the same bot
every already-stored message is bound to. Comparing `existing != message` at that point is
exactly "same content, same binding," which is the right definition of "the same message
again": pydantic's `__eq__` includes the private `_bot` attribute, so two structurally equal
messages bound to the same bot compare equal, and a genuinely different message (different
text, different sender, or one that was never the same message to begin with) does not.

Rejected: comparing by identity (`existing is message`). Two structurally identical copies of
the same source message minted by two separate `feed()` calls — the two-environment recipe fed
twice — are not the same object, and identity comparison would misclassify that redelivery as
a collision.

### D3. `bot_env_wait_timeout` is a fixture, not a `bot_env` parameter

The plugin already has the shape for this: `bot_blueprint` and `bot_dispatcher` are
independent, overridable value fixtures that `bot_env` depends on. Adding
`bot_env_wait_timeout` the same way — a fixture returning `DEFAULT_WAIT_TIMEOUT` that
`bot_env` reads and forwards as `default_wait_timeout=` — means a project overrides exactly
one fixture instead of reconstructing the whole `bot_env` body, which is the complaint this
closes.

### D4. `ensure_private_chat` duck-types instead of importing `UserSpec`

`aiogram.test.blueprint` imports from `aiogram.test.world` at module scope, so `world.py`
cannot import `UserSpec` from `blueprint.py` at module scope without a cycle — which is why
the existing `UserSpec` reference in `world.py`'s type hints is already `TYPE_CHECKING`-only.

`ensure_private_chat(user: UserState | UserSpec | int)` therefore resolves without an
`isinstance(user, UserSpec)` check: `UserState` is checked first and passed through unchanged
(trusted as already resolved — the only way to hold one is to have gotten it from this world),
`int` is checked second, and anything else is assumed to expose `.id` and is resolved through
`self.user(user.id)`. `UserSpec` is the only third type the signature admits, so this is not
looser than an explicit `isinstance` in practice, and it costs no runtime import.

### D5. The `looptime` note is corrected, not restructured

The old note was defensively correct but pointed at the wrong culprit — "a connection with
its own timeout may genuinely drop" describes a risk `looptime` does not create (a real
blocking call stays real-time, which is a limitation, not a hazard the fake clock introduces).
Field measurement against Mongo and Redis found the actual mine: async drivers schedule their
own deadlines (`serverSelectionTimeoutMS`, `socket_timeout`) through the same
`loop.call_later`/`loop.call_at` primitives `looptime` virtualizes, so a large virtual-time
jump can exhaust a driver's real deadline while the actual I/O it's timing takes milliseconds.
This is purely a documentation correction — no code changed, and no spec claim needed
amending, since the note was never a stated requirement.

## Testing

- `test_world.py`: a regression test builds two worlds, assigns one's registry to the other's
  `chats`, and asserts the new registry's identity, the carried chat's rewired `.world`, and
  that a chat added afterward to *either* world lands in the correct one — the case the naive
  `isinstance` guard missed.
- `test_environment.py`: one test collides two independently-allocated same-id messages from
  two foreign environments into one destination and asserts `WorldLookupError`; a second test
  re-feeds the same carried message a second time (through a fresh `Update` wrapper, so it is
  a distinct detached copy) and asserts no error and no duplicate entry.
- `test_plugin.py`: the fixture's default value, the override argument threading through
  `call_fixture`, and a subprocess-driven real pytest run overriding `bot_env_wait_timeout` in
  a project file and asserting `bot_env.world.default_wait_timeout` picked it up.
- `test_world.py`: `ensure_private_chat` exercised with a bare id and with a `UserSpec` off a
  real `Blueprint`, plus the existing-behavior check that an undeclared id still raises
  `WorldLookupError`.
