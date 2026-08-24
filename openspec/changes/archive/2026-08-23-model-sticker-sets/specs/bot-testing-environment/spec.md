## ADDED Requirements

### Requirement: Sticker sets are world state

The environment SHALL hold sticker sets by name, each carrying its title, sticker type and
the stickers it contains. A blueprint SHALL be able to declare existing sets, and every
environment built from it SHALL start from an independent copy.

#### Scenario: A declared set is readable

- **WHEN** a blueprint declares a sticker set and a handler calls `getStickerSet`
- **THEN** the declared set is returned without it having been created through the API

#### Scenario: Sets are isolated between environments

- **WHEN** two environments are built from one blueprint and one of them adds a sticker
- **THEN** the other still reports the declared contents

### Requirement: The sticker set lifecycle is modeled

Creating a set, adding, deleting and replacing its stickers, renaming it and deleting it
SHALL be applied to that registry, and `getStickerSet` SHALL report the result. Each SHALL
fail with `TelegramBadRequest` where Telegram would: a name already taken, a set that does
not exist, or a sticker that is not in the set.

#### Scenario: Create then add then read back

- **WHEN** a handler creates a set, adds a sticker to it, and calls `getStickerSet`
- **THEN** the returned set carries both the original and the added sticker

#### Scenario: A bot can check a set before writing to it

- **WHEN** a handler reads a set to decide whether it is full, then adds a sticker
- **THEN** the count it read reflects the stickers actually in the set

#### Scenario: Creating a set whose name is taken fails

- **WHEN** a handler creates a set with a name that already exists
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Reading or writing an unknown set fails

- **WHEN** a handler reads, renames, deletes or adds to a set that does not exist
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Removing a sticker that is not in the set fails

- **WHEN** a handler deletes or replaces a sticker the set does not contain
- **THEN** the call raises `TelegramBadRequest`

#### Scenario: Deleting a set removes it

- **WHEN** a handler deletes a set and then reads it
- **THEN** the read raises `TelegramBadRequest`

### Requirement: Sticker files are seeded, not modeled

`uploadStickerFile` SHALL return a stable file identifier the set methods can then
reference, and `getCustomEmojiStickers` SHALL echo the identifiers it was asked for. Neither
SHALL imply that sticker image data exists.

#### Scenario: An uploaded file can be added to a set

- **WHEN** a handler uploads a sticker file and adds the returned identifier to a set
- **THEN** the set reports a sticker carrying that identifier

#### Scenario: Custom emoji lookups echo their input

- **WHEN** a handler requests custom emoji stickers by identifier
- **THEN** one sticker is returned per requested identifier, carrying it

### Requirement: Per-sticker attributes stay record-only

Setting a sticker's emoji list, keywords, mask position or position in a set, and setting
either kind of set thumbnail, SHALL remain recorded and synthesized rather than modeled:
nothing reads them back, and thumbnails are media processing.

#### Scenario: An attribute setter is recorded but changes nothing

- **WHEN** a handler sets a sticker's keywords
- **THEN** the call succeeds and is visible in the call log, and the stored set is unchanged
