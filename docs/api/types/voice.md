# Voice

## Description

This object represents a voice note.


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file, which can be used to download or reuse the file |
| `file_unique_id` | `#!python str` | Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file. |
| `duration` | `#!python int` | Duration of the audio in seconds as defined by sender |
| `mime_type` | `#!python Optional[str]` | Optional. MIME type of the file as defined by sender |
| `file_size` | `#!python Optional[int]` | Optional. File size |



## Location

- `from aiogram.types import Voice`
- `from aiogram.api.types import Voice`
- `from aiogram.api.types.voice import Voice`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#voice)
- [How to download file?](../download_file.md)
