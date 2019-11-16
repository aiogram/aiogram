# Sticker

## Description

This object represents a sticker.


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file |
| `width` | `#!python int` | Sticker width |
| `height` | `#!python int` | Sticker height |
| `is_animated` | `#!python bool` | True, if the sticker is animated |
| `thumb` | `#!python Optional[PhotoSize]` | Optional. Sticker thumbnail in the .webp or .jpg format |
| `emoji` | `#!python Optional[str]` | Optional. Emoji associated with the sticker |
| `set_name` | `#!python Optional[str]` | Optional. Name of the sticker set to which the sticker belongs |
| `mask_position` | `#!python Optional[MaskPosition]` | Optional. For mask stickers, the position where the mask should be placed |
| `file_size` | `#!python Optional[int]` | Optional. File size |



## Location

- `from aiogram.types import Sticker`
- `from aiogram.api.types import Sticker`
- `from aiogram.api.types.sticker import Sticker`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sticker)
- [aiogram.types.MaskPosition](../types/mask_position.md)
- [aiogram.types.PhotoSize](../types/photo_size.md)
