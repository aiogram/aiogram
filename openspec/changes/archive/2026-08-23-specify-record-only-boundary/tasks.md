## 1. The list

- [x] 1.1 Add `RECORD_ONLY: frozenset[type[TelegramMethod[Any]]]` to `modeling.py` beside `REGISTRY`, grouped by reason with a comment per group (design D2, D3)
- [x] 1.2 Populate it from the surfaces named in the proposal, plus four the proposal did not enumerate but that belong on the same footing: per-sticker attributes and thumbnails, bot-instance lifecycle (`close`/`logOut`), game scores, and inert reads (`getForumTopicIconStickers`, `getUserChatBoosts`, `setUserEmojiStatus`) — 48 methods in 13 reason-groups
- [x] 1.3 Confirm every entry is currently unmodeled, so the change starts consistent

## 2. The guard

- [x] 2.1 Add a test asserting `RECORD_ONLY` and the modeled registry do not overlap (design D1)
- [x] 2.2 Add a comment on the test stating why it is *not* a completeness check, so a future reader does not "fix" it into one
- [x] 2.3 Verify the guard fails when a record-only method is added to the registry

## 3. Documentation

- [x] 3.1 Add a "What stays record-only" section to `docs/dispatcher/testing.rst`, grouped by reason
- [x] 3.2 List the deferred clusters separately, framed as candidates rather than refusals
- [x] 3.3 Build docs and fix any new warnings

## 4. Release readiness

- [x] 4.1 No new fragment: the toolkit has not shipped, so a clause was folded into its existing `CHANGES/1874.feature.rst` entry
- [x] 4.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
