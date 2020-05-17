# Document

## Description

This object represents a general file (as opposed to photos, voice messages and audio files).


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file, which can be used to download or reuse the file |
| `file_unique_id` | `#!python str` | Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file. |
| `thumb` | `#!python Optional[PhotoSize]` | Optional. Document thumbnail as defined by sender |
| `file_name` | `#!python Optional[str]` | Optional. Original filename as defined by sender |
| `mime_type` | `#!python Optional[str]` | Optional. MIME type of the file as defined by sender |
| `file_size` | `#!python Optional[int]` | Optional. File size |



## Location

- `from aiogram.types import Document`
- `from aiogram.api.types import Document`
- `from aiogram.api.types.document import Document`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#document)
- [aiogram.types.PhotoSize](../types/photo_size.md)
- [How to download file?](../download_file.md)
