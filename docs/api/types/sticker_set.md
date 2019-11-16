# StickerSet

## Description

This object represents a sticker set.


## Attributes

| Name | Type | Description |
| - | - | - |
| `name` | `#!python str` | Sticker set name |
| `title` | `#!python str` | Sticker set title |
| `is_animated` | `#!python bool` | True, if the sticker set contains animated stickers |
| `contains_masks` | `#!python bool` | True, if the sticker set contains masks |
| `stickers` | `#!python List[Sticker]` | List of all set stickers |



## Location

- `from aiogram.types import StickerSet`
- `from aiogram.api.types import StickerSet`
- `from aiogram.api.types.sticker_set import StickerSet`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#stickerset)
- [aiogram.types.Sticker](../types/sticker.md)
