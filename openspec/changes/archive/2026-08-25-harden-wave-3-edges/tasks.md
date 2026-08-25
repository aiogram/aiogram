# Tasks

## 1. Foreign chat-registry assignment

- [x] 1.1 Widen `World.__setattr__`'s guard to
      `not isinstance(value, ChatRegistry) or value.world is not self` (design D1)
- [x] 1.2 Regression test in `test_world.py`: `w2.chats = w1.chats` installs a registry wired
      to `w2`, the carried chat is rewired to `w2`, and a chat added afterward to either world
      lands in the correct one

## 2. Loud carried-message id collision

- [x] 2.1 `_register_carried_message` raises `WorldLookupError` when the destination chat
      holds a *different* message under the incoming id, naming both via `describe_message`
      (design D2)
- [x] 2.2 An equal message under the same id — same content, same bot binding — stays a
      silent no-op
- [x] 2.3 Test: two foreign environments each allocate the same first message id in the same
      declared chat; feeding both into one destination raises on the second
- [x] 2.4 Test: feeding the same carried message a second time, through a fresh `Update`
      wrapper, is not an error and does not duplicate the chat's messages

## 3. `bot_env_wait_timeout` fixture

- [x] 3.1 Add `bot_env_wait_timeout` fixture returning `DEFAULT_WAIT_TIMEOUT` in `plugin.py`
      (design D3)
- [x] 3.2 `bot_env` depends on it and forwards it as `default_wait_timeout=`
- [x] 3.3 Test: default value; override argument reaches `BotTestEnvironment` through
      `call_fixture`; a subprocess pytest run overriding the fixture in a project file shows
      `bot_env.world.default_wait_timeout` picked it up

## 4. `ensure_private_chat` widened signature

- [x] 4.1 `World.ensure_private_chat(user: UserState | UserSpec | int)`, resolving through
      `World.user` for the non-`UserState` forms (design D4)
- [x] 4.2 Update `modeling.py`'s undeclared-private-chat hint to the one-argument form
- [x] 4.3 Test: a bare id and a `UserSpec` off a real `Blueprint` both resolve the same chat
      an already-resolved `UserState` would; an undeclared id still raises `WorldLookupError`

## 5. Documentation

- [x] 5.1 Rewrite the `looptime` limits note in `docs/dispatcher/testing.rst` to name
      virtualized driver deadlines as the hazard, with the measured 60s-virtual /
      0.05s-real ratio (design D5)
- [x] 5.2 Replace the `bot_env` fixture-copy example for `default_wait_timeout` with the new
      `bot_env_wait_timeout` fixture
- [x] 5.3 Drop the two-step `ensure_private_chat(world.user(...))` form from the undeclared
      private-chat section

## 6. Spec sync

- [x] 6.1 `bot-testing-environment`: extend the chat-registry binding requirement and scenario
      to cover a foreign registry assignment; extend the carried-message rule with the
      collision and equal-redelivery scenarios
- [x] 6.2 `bot-testing-pytest`: extend the fixture-set requirement with the wait-timeout value
      fixture and its override scenario

## 7. Release readiness

- [x] 7.1 No new fragment: folded into the toolkit's existing `CHANGES/1887.feature.rst` entry
- [x] 7.2 Full check loop green: `ruff format`, `ruff check --show-fixes --preview aiogram
      examples`, `mypy aiogram`, `pytest tests -q` at 100% coverage for the touched modules
