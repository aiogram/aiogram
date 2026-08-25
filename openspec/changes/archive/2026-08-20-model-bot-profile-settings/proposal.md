## Why

Every real bot has startup code that configures its own profile — `setMyCommands` per
scope and language, `setMyName`, `setMyDescription`, `setChatMenuButton`,
`setMyDefaultAdministratorRights` — and that code is currently untestable. The setters are
answered with `True` and forgotten; the matching getters return synthesized noise, so
`get_my_commands()` after `set_my_commands([...])` returns a list unrelated to what was
just set. A test can only assert that a call was made, never that the configuration is
correct, which is precisely the thing that goes wrong: a command registered under the
wrong scope, a description set for the wrong language, a menu button configured for a chat
that should have inherited the default.

Thirteen methods are involved and they share one data shape: a value keyed by scope and
language. This is the highest value-to-cost ratio left in the API surface — one small
state object, no fidelity risk (Telegram has no hidden behavior here beyond the
scope-resolution fallback), and it makes an entire category of startup code assertable.

## What Changes

- **New `BotProfileState` on the world**, holding the bot's own configuration: commands,
  name, description, short description, default administrator rights, and menu buttons.
  Values are keyed by scope and language code where the Bot API keys them that way.
- **Setters write, getters read.** `SetMyCommands`, `DeleteMyCommands`, `SetMyName`,
  `SetMyDescription`, `SetMyShortDescription`, `SetMyDefaultAdministratorRights` and
  `SetChatMenuButton` mutate that state; `GetMyCommands`, `GetMyName`, `GetMyDescription`,
  `GetMyShortDescription`, `GetMyDefaultAdministratorRights` and `GetChatMenuButton` read
  it back.
- **Exact-key lookup, as Telegram documents it.** `getMyCommands` returns what was set for
  that exact scope and language pair and an empty list otherwise — it does *not* fall back
  to a higher-level scope. The documented fallback ("higher level commands will be shown
  to affected users") describes what users see, not what the getter returns, and modeling
  it would make the fake disagree with the real API.
- **Documented defaults for unset values**: an empty command list, an empty description
  and short description, `MenuButtonDefault`, all-`False` administrator rights, and the
  bot's own `first_name` for an unset name.
- **Blueprint declaration** of the bot's initial profile, so a test can start from a
  configured bot rather than driving the setters first.

No breaking changes: tests asserting on `env.calls` for these methods keep passing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: the modeled method set grows to cover the bot's own profile
  configuration, and the environment gains a requirement that setter/getter pairs
  round-trip through world state with Telegram's scope and language fallback.

## Impact

- **Code**: `aiogram/test/world.py` (new `BotProfileState`), `blueprint.py` (declaring an
  initial profile), `modeling.py` (13 handlers, all thin).
- **Tests**: new module under `tests/test_testing/`, holding the package at 100%. The
  scope/language keying deserves parametrized coverage rather than hand-written cases.
- **Docs**: a "Bot profile configuration" section in `docs/dispatcher/testing.rst`.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Compatibility**: no new dependencies; Python 3.10–3.14 and PyPy 3.11 as before.
- **Risk**: low, and bounded. These methods have no server-side behavior beyond storing
  and returning a value, so the fake can be faithful by construction. The one judgement
  call — not inventing a scope fallback the getter does not have — is recorded in the
  design.
