# InlineQueryResultCachedVideo

## Description

Represents a link to a video file stored on the Telegram servers. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the video.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be video |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `video_file_id` | `#!python str` | A valid file identifier for the video file |
| `title` | `#!python str` | Title for the result |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the video to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the video |



## Location

- `from aiogram.types import InlineQueryResultCachedVideo`
- `from aiogram.api.types import InlineQueryResultCachedVideo`
- `from aiogram.api.types.inline_query_result_cached_video import InlineQueryResultCachedVideo`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcachedvideo)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
