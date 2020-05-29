# PhotoSize

## Description

This object represents one size of a photo or a file / sticker thumbnail.


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file, which can be used to download or reuse the file |
| `file_unique_id` | `#!python str` | Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file. |
| `width` | `#!python int` | Photo width |
| `height` | `#!python int` | Photo height |
| `file_size` | `#!python Optional[int]` | Optional. File size |



## Location

- `from aiogram.types import PhotoSize`
- `from aiogram.api.types import PhotoSize`
- `from aiogram.api.types.photo_size import PhotoSize`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#photosize)
- [How to download file?](../download_file.md)
