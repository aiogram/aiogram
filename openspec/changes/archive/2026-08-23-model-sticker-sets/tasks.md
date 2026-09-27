## 1. The registry

- [x] 1.1 Add `StickerSetState` (name, title, sticker type, stickers) and `World.sticker_sets` keyed by name (design D1, D2)
- [x] 1.2 Add a lookup that raises `TelegramBadRequest` for an unknown name
- [x] 1.3 Add a `Blueprint` declaration for existing sets
- [x] 1.4 Tests: declared set is readable; environments stay isolated

## 2. Lifecycle methods

- [x] 2.1 Model `CreateNewStickerSet`, rejecting a name already taken
- [x] 2.2 Model `AddStickerToSet` and `DeleteStickerFromSet`
- [x] 2.3 Model `ReplaceStickerInSet` as delete-then-add at the same position (design D3)
- [x] 2.4 Model `SetStickerSetTitle` and `DeleteStickerSet`
- [x] 2.5 Model `GetStickerSet` reading the registry
- [x] 2.6 Raise `TelegramBadRequest` for an unknown set and for a sticker the set does not contain
- [x] 2.7 Tests per method: resulting set contents, and each error path

## 3. Seeded answers

- [x] 3.1 `UploadStickerFile`: return a stable file id from the world counter, registering no content (design D4)
- [x] 3.2 `GetCustomEmojiStickers`: return one sticker per requested identifier, echoing it
- [x] 3.3 Tests: an uploaded id can be added to a set and read back; the emoji lookup echoes its input

## 4. Explicit record-only

- [x] 4.1 Leave `SetStickerEmojiList`, `SetStickerKeywords`, `SetStickerMaskPosition`, `SetStickerPositionInSet`, `SetStickerSetThumbnail` and `SetCustomEmojiStickerSetThumbnail` unmodeled
- [x] 4.2 Confirmed they were already in `RECORD_ONLY` with their reason — no edit needed, and the anti-overlap guard proves the lifecycle methods left it
- [x] 4.3 Test: an attribute setter is recorded and the stored set is unchanged

## 5. Documentation

- [x] 5.1 Add a "Sticker sets" section to `docs/dispatcher/testing.rst`
- [x] 5.2 State the non-goals: no image data, no pack limits, no naming convention, and the attribute setters staying record-only
- [x] 5.3 Build docs and fix any new warnings

## 6. Release readiness

- [x] 6.1 No new fragment: the toolkit is unreleased, so this folded into its existing `CHANGES/1874.feature.rst` entry
- [x] 6.2 Full check loop green: `rtk ruff format`, `rtk ruff check --show-fixes --preview aiogram examples`, `rtk mypy aiogram`, `rtk test uv run pytest tests -q --cov=aiogram --cov-report=term-missing` at 100%
- [x] 6.3 Confirm the synthesis guard over every generated return type still passes
- [x] 6.4 Removed the sticker-set cluster from the deferred lists in `RECORD_ONLY`'s comment and in the docs
