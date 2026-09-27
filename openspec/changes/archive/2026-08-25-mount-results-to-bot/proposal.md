## Why

The first real bot driven through the toolkit — a production Mafia-game group bot — broke on
its second line:

```python
message = await bot.send_message(chat_id=group.id, text="Night falls")
await message.edit_text("Dawn")          # RuntimeError: bot is not attached
```

A real session parses every response with ``context={"bot": bot}``, and pydantic threads that
context through the whole object tree — which is what makes ``message.answer()``,
``message.delete()`` and the shortcuts of nested objects such as ``reply_to_message`` work on
whatever a call returned. The fake *constructs* its results rather than parsing them, so that
context never ran and every shortcut on every result raised. The same held for anything read
straight out of the world: ``chat.messages[-1].answer(...)`` raised on a message a user actor
had sent, because no call ever returned it.

There was a second, quieter failure underneath. ``Dispatcher.feed_update`` re-mounts an update
carrying a foreign bot by dumping it to JSON and validating it again, which mints copies of
everything inside — so a handler received a *twin* of the message the chat stored. An edit
applied through the handler's object landed on an orphan, and ``message is chat.messages[-1]``
was false, which is exactly the assertion a state-based test wants to make.

And the traffic runs both ways. A test that shares a module-level ``reply_markup`` constant
across its whole file passed that very object into ``send_message``; the world stored it,
mounted it to a bot, and from then on the constant compared unequal to its own unbound twin
in every later test — while printing identically, because the repr hides the binding.

## What Changes

- **Everything entering or leaving the fake world is bound to the environment's bot**, the
  way production binds parsed responses. Results of modeled, synthesized and overridden calls
  are mounted on the way out of the session; messages are mounted as they are *stored*, so a
  message a user actor sent, and a service message no result ever carried, are as usable as
  one a call returned.
- **Ownership is a rule, not an optimization.** An object that already carries a bot belongs
  to the world, and a later caller never re-binds it. That is what keeps the documented recipe
  for a bot sending through a module-level ``Bot`` honest: the singleton shares the session,
  but the world's objects keep resolving their defaults against the environment's bot.
- **Handlers receive the world's own objects.** An update is mounted before it reaches
  ``feed_update``, which skips the dispatcher's JSON round-trip, so
  ``received_message is chat.messages[-1]`` holds and an edit through either lands on both.
- **A test's own objects stay the test's own.** Every method is copied once at the
  ``handle_call`` choke point, after the call log has recorded the caller's object, so a
  handler may store whatever it reads off the method. Value objects the world stores —
  permissions, a photo, a command list, a menu button — are copied on the way *out* as well,
  so reading them back does not bind the world's state. Messages are the deliberate exception:
  a returned message *is* the stored one.
- **Declared override results are copied per call**, so a canned object declared once at
  module level is neither mutated by the call it describes nor left holding a reference to a
  disposed environment.
- **A failing ``==`` between two objects that differ only in their binding explains itself**
  through the plugin's assertion hook, rather than printing two identical-looking reprs.

No API is removed. The observable change is that shortcuts work everywhere and that identity
now means what a test would assume it means.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: gains the binding and copy rules as stated behavior — results
  and stored objects carry the bot, handlers receive the world's own objects, and the
  boundary in both directions is a copy.
- `bot-testing-pytest`: the readable-failure requirement is extended to the comparison this
  binding rule makes possible — two objects with identical payloads and different owners.

## Impact

- **Code**: a new `aiogram/test/mounting.py` owning both halves of the policy (`mount`,
  `detach`, `detached_copy`, `bindables`, `bound_elsewhere`); `session.py` mounts every
  answer; `environment.py` copies in at `handle_call` and mounts updates in `feed`;
  `world.py` grows `World.bind`, a `ChatRegistry` that hands each chat a way back to the
  world, and `derive_message`; `overrides.py` hands out copies; `plugin.py` explains a
  binding-only inequality.
- **Tests**: a new `tests/test_testing/test_mounting.py` for the walk itself, plus suites in
  `test_session.py` and `test_environment.py` covering both directions of the boundary.
- **Docs**: an "Everything carries the bot" section in `docs/dispatcher/testing.rst`.
- **Changelog**: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry.
- **Risk**: the walk runs on every call and every trigger, so it must be cheap and must not
  recurse — both addressed in the design. The subtler risk is a handler that stores something
  it read off a method and *is* the caller's object; that risk is what moving the copy to the
  choke point removes.
