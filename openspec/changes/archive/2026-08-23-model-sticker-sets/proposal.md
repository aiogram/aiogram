## Why

A sticker-pack bot's own logic branches on the pack: how many stickers it holds, whether a
set with that name already exists, whether the sticker it just added is really there. Today
`getStickerSet` returns a synthesized set unrelated to anything the bot created, so
`createNewStickerSet` → `addStickerToSet` → `getStickerSet` returns a stranger, and the
"pack is full" branch is never the branch a test takes.

The cluster is coherent and self-describing: seven methods that all read or write one
registry, and `getStickerSet` exists precisely so a bot can check before it writes. Modeled
individually they are pointless; together they make "my pack now holds three stickers
titled X" assertable.

This is the smallest-demand change in the plan and is proposed as a *candidate*: it is
listed among the deferred clusters rather than the record-only surfaces, and it should be
built when someone reports needing it rather than on principle.

## What Changes

- **A sticker set registry.** `StickerSetState` holds a set's name, title, sticker type and
  its stickers; `World.sticker_sets` is keyed by name, as Telegram keys them.
- **The lifecycle is modeled**: `CreateNewStickerSet`, `AddStickerToSet`,
  `DeleteStickerFromSet`, `ReplaceStickerInSet`, `SetStickerSetTitle`, `DeleteStickerSet`,
  and `GetStickerSet` reading it back.
- **Errors match the mistakes a pack bot makes**: creating a set whose name is taken,
  reading or writing a set that does not exist, removing a sticker that is not in it.
- **A blueprint declares existing sets**, so a test can start from a pack rather than
  building one.
- **`UploadStickerFile` and `GetCustomEmojiStickers` are seeded**, not modeled: the upload
  returns a stable file id the create and add methods can then reference, and the custom
  emoji lookup echoes the ids it was asked for.
- **The per-sticker attribute setters stay record-only** — `SetStickerEmojiList`,
  `SetStickerKeywords`, `SetStickerMaskPosition`, `SetStickerPositionInSet`, and both
  thumbnail setters. Nothing reads them back, and thumbnails are media processing.

No breaking changes: tests asserting on `env.calls` for these methods keep passing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bot-testing-environment`: sticker sets become world state, with their lifecycle methods
  modeled and the per-sticker attribute setters explicitly left record-only.

## Impact

- **Code**: `aiogram/test/world.py` (`StickerSetState`, `World.sticker_sets`),
  `blueprint.py` (declaring sets), `modeling.py` (seven handlers plus two seeded answers).
- **Tests**: a new module under `tests/test_testing/`, holding the package at 100%.
- **Docs**: a "Sticker sets" section in `docs/dispatcher/testing.rst`.
- **Changelog**: `CHANGES/<issue-or-pr>.feature.rst`.
- **Risk**: low. The cluster is closed — nothing else in the world reads sticker sets — and
  sticker *files* stay synthesized, so there is no half-modeled edge where a test might
  expect real image data.
