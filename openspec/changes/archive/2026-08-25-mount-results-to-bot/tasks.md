## 1. The binding mechanism

- [x] 1.1 Add `aiogram/test/mounting.py` owning both halves of the policy, with `bindables()`
      as the single iterative walk underneath all of them (design D1)
- [x] 1.2 `mount(value, bot)`: bind every unbound node, prune at owned ones (design D3)
- [x] 1.3 `detach(value)` / `detached_copy(value, bot=...)`: produce objects nobody owns, or
      owned by a named bot (design D7)
- [x] 1.4 `bound_elsewhere(value, bot)`: identity comparison, because two bots built from one
      blueprint compare equal (design D3)
- [x] 1.5 Walk `__pydantic_extra__` as well as `__dict__`, so fields from a future Bot API
      version are mounted too
- [x] 1.6 Tests: a deep reply chain is mounted without recursing; a self-referential result
      terminates; a `URLInputFile` carrying a bot is shared rather than cloned

## 2. Results carry the bot

- [x] 2.1 Mount every answer in `FakeTelegramSession.make_request` — the one place modeled,
      synthesized and overridden results all pass through
- [x] 2.2 Tests: shortcuts work on a result, on objects nested inside it, on every item of a
      list result, and on an overridden result

## 3. The world owns what it stores

- [x] 3.1 Bind in `ChatState.add_message`, the moment every producer shares (design D2)
- [x] 3.2 Add `World.bind(bot)` for content stored before the environment had one, and call it
      from `BotTestEnvironment.__init__`
- [x] 3.3 Derive `ChatState.bound_bot` from the world instead of storing a copy (design D4)
- [x] 3.4 Add `ChatRegistry`, installing the world backref through `__setitem__`, `update`,
      `setdefault` and `|=` (design D4)
- [x] 3.5 Add `derive_message` as the single path for edits, forwards and copies, copying only
      the changes and binding the shell explicitly
- [x] 3.6 Tests: a message a user sent is mounted; a service message nobody returned is
      mounted; a second bot sharing the session does not steal a stored message but does get
      its own fresh results

## 4. Handlers receive the world's own objects

- [x] 4.1 Mount the update in `BotTestEnvironment.feed` before `feed_update`, in one pass that
      also detects a foreign owner (design D8)
- [x] 4.2 Copy an update that belongs to another environment, and register the message it
      carries in the destination chat, advancing that chat's allocator (design D8)
- [x] 4.3 Tests: `received is chat.messages[-1]`; an actor-built update is fed without a copy;
      an update from another environment is copied and its reply does not collide with it; a
      message for an undeclared chat is left alone

## 5. The caller's objects stay the caller's

- [x] 5.1 Copy the resolved method once in `handle_call`, after the call log records the
      caller's own object (design D5)
- [x] 5.2 Remove the eight hand-written copies from `modeling.py` and state the boundary in
      its module docstring, where the next handler is written
- [x] 5.3 Copy the caller's values out of a trigger's `fields=` / `reaction=` too, leaving
      objects that already belong to this environment's bot untouched
- [x] 5.4 Tests: a module-level `reply_markup` constant is not captured, by a send or by an
      edit; entities are not captured; an unguarded handler stores a copy; a disposed
      environment is not kept alive by a constant

## 6. The world's value objects stay the world's

- [x] 6.1 Copy out of `getChat` (permissions, photo), `getMyCommands`,
      `getMyDefaultAdministratorRights` and `getChatMenuButton` (design D6)
- [x] 6.2 Leave messages shared — a returned message is the stored one
- [x] 6.3 Tests: `getChat` does not hand out the stored permissions or photo; a returned
      message is still the stored one

## 7. Overrides

- [x] 7.1 `Outcome.apply` returns a `detached_copy` of the declared result, bound to the
      calling bot as it is made (design D9)
- [x] 7.2 Tests: a declared result is not mutated by the call it describes; a repeated
      override answers each call with its own object

## 8. Failure reporting

- [x] 8.1 Explain a comparison between two objects that differ only in their binding, pointing
      at `model_dump()` (design D10)
- [x] 8.2 Guard the dump, so a graph too deep to serialize gets no explanation rather than a
      traceback replacing the user's own failure
- [x] 8.3 Tests: the explanation appears; objects that really differ are left alone; a graph
      too deep to dump gets no explanation; unrelated comparisons are untouched

## 9. Documentation

- [x] 9.1 Add an "Everything carries the bot" section to `docs/dispatcher/testing.rst`
- [x] 9.2 State the three consequences — results usable, world state usable, handlers get the
      world's own objects — and the copy rule in both directions
- [x] 9.3 Explain the binding-only inequality and show `model_dump()` as the comparison
- [x] 9.4 Document the global-`Bot` recipe and what the singleton does *not* take over
- [x] 9.5 Build docs and fix any new warnings

## 10. Release readiness

- [x] 10.1 No new fragment: the toolkit is unreleased, so this folded into its existing
      `CHANGES/1887.feature.rst` entry
- [x] 10.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview
      aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q
      --cov=aiogram --cov-report=term-missing` at 100%
