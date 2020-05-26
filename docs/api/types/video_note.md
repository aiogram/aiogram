# VideoNote

## Description

This object represents a video message (available in Telegram apps as of v.4.0).


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file, which can be used to download or reuse the file |
| `file_unique_id` | `#!python str` | Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file. |
| `length` | `#!python int` | Video width and height (diameter of the video message) as defined by sender |
| `duration` | `#!python int` | Duration of the video in seconds as defined by sender |
| `thumb` | `#!python Optional[PhotoSize]` | Optional. Video thumbnail |
| `file_size` | `#!python Optional[int]` | Optional. File size |



## Location

- `from aiogram.types import VideoNote`
- `from aiogram.api.types import VideoNote`
- `from aiogram.api.types.video_note import VideoNote`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#videonote)
- [aiogram.types.PhotoSize](../types/photo_size.md)
- [How to download file?](../download_file.md)
