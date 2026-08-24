## 1. Profile state

- [x] 1.1 Add `BotProfileState` to `world.py` with per-field dicts for commands, name, description, short description, default administrator rights and menu buttons (design D1)
- [x] 1.2 Implement `BotCommandScope` → hashable key normalization from the member's own fields, with an omitted scope keying identically to an explicit default (design D5)
- [x] 1.3 Attach `BotProfileState` to `World` next to `bot_user`
- [x] 1.4 Tests: key normalization per scope variant, parametrized over every `BotCommandScope` union member

## 2. Blueprint declaration

- [x] 2.1 Add a frozen bot-profile declaration to `Blueprint` (design D4)
- [x] 2.2 Deep-copy it in `Blueprint.build()` so environments stay isolated
- [x] 2.3 Tests: declared profile is readable without any setter call; two environments from one blueprint do not observe each other's writes

## 3. Setters

- [x] 3.1 Implement a shared write helper parametrized by field and key extractor (risk mitigation for repetitive handlers)
- [x] 3.2 Model `SetMyCommands`, `DeleteMyCommands`, `SetMyName`, `SetMyDescription`, `SetMyShortDescription`
- [x] 3.3 Model `SetMyDefaultAdministratorRights` (keyed by `for_channels`) and `SetChatMenuButton` (keyed by `chat_id`, `None` for the default)
- [x] 3.4 Tests: each setter writes only its own key; deleting one scope leaves others intact

## 4. Getters

- [x] 4.1 Model `GetMyCommands` as an exact-key read, and the localized texts and menu button with their documented fallback (design D2)
- [x] 4.2 Return the documented default for an unset key, including `bot_user.first_name` for an unset name (design D3)
- [x] 4.3 Tests: round-trip per method; commands do not fall back across scope or language; unconfigured environment returns documented defaults for all six
- [x] 4.4 Tests: a localized text falls back to the default language, a dedicated language wins, and clearing one restores the fallback
- [x] 4.5 Tests: a per-chat menu button overrides the default and an unknown chat fails

## 5. Documentation

- [x] 5.1 Add a "Bot profile configuration" section to `docs/dispatcher/testing.rst`
- [x] 5.2 State explicitly that commands do not fall back across scope or language while the localized texts do fall back by language, and why (design D2)
- [x] 5.3 Note that the bot's profile photo methods stay record-only
- [x] 5.4 Build docs and fix any new warnings

## 6. Release readiness

- [x] 6.1 `CHANGES/<issue-or-pr>.feature.rst`, noting that these getters now return documented defaults instead of synthesized content
- [x] 6.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 6.3 Confirm the parametrized synthesis guard over every generated return type still passes
