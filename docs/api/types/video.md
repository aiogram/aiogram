# Video

## Description

This object represents a video file.


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file, which can be used to download or reuse the file |
| `file_unique_id` | `#!python str` | Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file. |
| `width` | `#!python int` | Video width as defined by sender |
| `height` | `#!python int` | Video height as defined by sender |
| `duration` | `#!python int` | Duration of the video in seconds as defined by sender |
| `thumb` | `#!python Optional[PhotoSize]` | Optional. Video thumbnail |
| `mime_type` | `#!python Optional[str]` | Optional. Mime type of a file as defined by sender |
| `file_size` | `#!python Optional[int]` | Optional. File size |



## Location

- `from aiogram.types import Video`
- `from aiogram.api.types import Video`
- `from aiogram.api.types.video import Video`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#video)
- [aiogram.types.PhotoSize](../types/photo_size.md)
- [How to download file?](../download_file.md)
