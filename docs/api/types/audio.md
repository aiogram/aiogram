# Audio

## Description

This object represents an audio file to be treated as music by the Telegram clients.


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file, which can be used to download or reuse the file |
| `file_unique_id` | `#!python str` | Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file. |
| `duration` | `#!python int` | Duration of the audio in seconds as defined by sender |
| `performer` | `#!python Optional[str]` | Optional. Performer of the audio as defined by sender or by audio tags |
| `title` | `#!python Optional[str]` | Optional. Title of the audio as defined by sender or by audio tags |
| `mime_type` | `#!python Optional[str]` | Optional. MIME type of the file as defined by sender |
| `file_size` | `#!python Optional[int]` | Optional. File size |
| `thumb` | `#!python Optional[PhotoSize]` | Optional. Thumbnail of the album cover to which the music file belongs |



## Location

- `from aiogram.types import Audio`
- `from aiogram.api.types import Audio`
- `from aiogram.api.types.audio import Audio`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#audio)
- [aiogram.types.PhotoSize](../types/photo_size.md)
- [How to download file?](../download_file.md)
