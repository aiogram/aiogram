## Why

Wave-2's hardening closed the field reports it was written against, but continued use of the
toolkit against the same production bot turned up a third round — smaller this time, all
edges the second pass didn't quite reach, plus one recipe note that field measurement showed
was blaming the wrong mechanism.

- `World.__setattr__`'s registry guard converts `world.chats = ...` whenever the value is not
  already a `ChatRegistry` — but `w2.chats = w1.chats` *is* already one. It passes untouched,
  so `w2.chats` becomes a live alias of `w1`'s registry: every chat added to `w2` afterward is
  inserted through `w1`'s `__setitem__` and wired to `w1`, bound to `w1`'s bot instead of
  `w2`'s. Exactly the bug the guard was written to close, one layer further down.
- `_register_carried_message` finds an id already taken in the destination chat and silently
  leaves the incoming message unregistered — even when what's already there is a genuinely
  different message. The handler processing the incoming update goes on to work on an object
  the world will never hold: nothing it does to that message is observable, and a
  `wait_for_message` waiting for it hangs for the full timeout with nothing in the failure
  message to explain why.
- Overriding `default_wait_timeout` meant copying the entire `bot_env` fixture body just to
  change one constructor argument, because the plugin exposed `bot_blueprint` and
  `bot_dispatcher` as overridable value fixtures but hard-coded the timeout inline.
- `World.ensure_private_chat` took only a `UserState`, so the common case —
  `world.ensure_private_chat(world.user(spec.id))` — spent its only argument on a lookup the
  method could have done itself, the same way `BotTestEnvironment.user` already accepts a
  spec or a bare id.
- The `looptime` note warned that a "connection with its own timeout may genuinely drop" under
  the virtual clock. Measurement against Mongo and Redis showed the opposite failure mode is
  the real one in practice: both drivers schedule their deadlines through the same
  `loop.call_later` `looptime` virtualizes, so a 60-virtual-second jump can burn a 30-second
  driver deadline in the middle of a real 50-millisecond handshake — invisible against a local
  database, a live hazard against a slow or remote one.

## What Changes

- **The registry guard checks ownership, not just type.** `World.__setattr__` rewraps a
  `chats` assignment whenever the value is not a `ChatRegistry` *or* is one that belongs to a
  different world, so `w2.chats = w1.chats` installs a registry wired to `w2` — a chat that
  comes along keeps its identity but is now correctly claimed by `w2`, and a chat added
  afterward through either world's registry is wired to that world alone. A registry already
  wired to `self` is still left alone by identity, so `world.chats = world.chats` stays a
  no-op.
- **A carried-message id collision is loud.** `_register_carried_message` raises
  `WorldLookupError` naming both messages when the destination chat already holds a
  *different* message under the incoming id. Re-registering an update that is already
  registered, or one that is structurally equal once bound to this environment's bot, stays
  the silent no-op it always was — the guard is on genuine collisions, not on redelivery.
- **`bot_env_wait_timeout` is a fixture of its own**, mirroring `bot_blueprint` and
  `bot_dispatcher`: the plugin's `bot_env` fixture takes it as a dependency and passes it
  through to `BotTestEnvironment(..., default_wait_timeout=...)`, so a project overrides one
  small fixture instead of rebuilding `bot_env`.
- **`World.ensure_private_chat` accepts a `UserSpec`, a `UserState` or a bare id** — the
  `UserState` a test already had, plus the spec-or-id pair `BotTestEnvironment.user` already
  accepts. A spec or an id is resolved through `World.user`, so an undeclared id is still
  refused with `WorldLookupError`; a `UserState` is
  trusted as already resolved.
- **The `looptime` limits paragraph is rewritten** to name the actual hazard — virtualized
  driver deadlines, not a genuinely blocking connection — with the measured
  60-virtual-seconds-to-0.05-real-seconds ratio as the concrete number, and advice to mark a
  test `looptime` only once its database calls are mocked, faked, or genuinely local.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the chat-registry binding requirement extends to a registry
  assigned from another world; the carried-message registration rule gains the collision
  case; `ensure_private_chat`'s accepted forms widen.
- `bot-testing-pytest`: the fixture set gains the wait-timeout value fixture.

## Impact

- **Code**: `world.py`'s `World.__setattr__` guard condition and `World.ensure_private_chat`
  signature; `environment.py`'s `_register_carried_message` gains the collision check and
  imports `describe_message`; `plugin.py` gains `bot_env_wait_timeout` and `bot_env` depends
  on it; `modeling.py`'s undeclared-private-chat hint is updated to the one-argument form.
- **Tests**: `test_world.py` (foreign-registry rewrap, `ensure_private_chat`'s widened forms),
  `test_environment.py` (loud collision, equal-content no-op), `test_plugin.py` (the new
  fixture's default, override reaching `bot_env` through a real pytest run).
- **Docs**: `docs/dispatcher/testing.rst`'s wait-timeout override example now shows the
  fixture instead of reconstructing `bot_env`; the `ensure_private_chat` mention in the
  undeclared-chat section drops the two-step form; the `looptime` limits note is rewritten.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry — the
  toolkit is unreleased, so there is no released behavior to describe a change to.
- **Risk**: the collision guard is a new way to fail a test that previously passed silently
  wrong; a suite that happened to rely on the old silent-drop behavior — feeding two updates
  whose carried messages collide by id and expecting only the first to register — now sees
  `WorldLookupError` instead. That is the fix working as intended: such a test was asserting
  on a message the world had already stopped tracking.
