# InlineQueryResultMpeg4Gif

## Description

Represents a link to a video animation (H.264/MPEG-4 AVC video without sound). By default, this animated MPEG-4 file will be sent by the user with optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the animation.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be mpeg4_gif |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `mpeg4_url` | `#!python str` | A valid URL for the MP4 file. File size must not exceed 1MB |
| `thumb_url` | `#!python str` | URL of the static thumbnail (jpeg or gif) for the result |
| `mpeg4_width` | `#!python Optional[int]` | Optional. Video width |
| `mpeg4_height` | `#!python Optional[int]` | Optional. Video height |
| `mpeg4_duration` | `#!python Optional[int]` | Optional. Video duration |
| `title` | `#!python Optional[str]` | Optional. Title for the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the MPEG-4 file to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the video animation |



## Location

- `from aiogram.types import InlineQueryResultMpeg4Gif`
- `from aiogram.api.types import InlineQueryResultMpeg4Gif`
- `from aiogram.api.types.inline_query_result_mpeg4_gif import InlineQueryResultMpeg4Gif`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultmpeg4gif)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
