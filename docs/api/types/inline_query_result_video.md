# InlineQueryResultVideo

## Description

Represents a link to a page containing an embedded video player or a video file. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the video.

If an InlineQueryResultVideo message contains an embedded video (e.g., YouTube), you must replace its content using input_message_content.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be video |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `video_url` | `#!python str` | A valid URL for the embedded video player or video file |
| `mime_type` | `#!python str` | Mime type of the content of video url, 'text/html' or 'video/mp4' |
| `thumb_url` | `#!python str` | URL of the thumbnail (jpeg only) for the video |
| `title` | `#!python str` | Title for the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the video to be sent, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Mode for parsing entities in the video caption. See formatting options for more details. |
| `video_width` | `#!python Optional[int]` | Optional. Video width |
| `video_height` | `#!python Optional[int]` | Optional. Video height |
| `video_duration` | `#!python Optional[int]` | Optional. Video duration in seconds |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the video. This field is required if InlineQueryResultVideo is used to send an HTML-page as a result (e.g., a YouTube video). |



## Location

- `from aiogram.types import InlineQueryResultVideo`
- `from aiogram.api.types import InlineQueryResultVideo`
- `from aiogram.api.types.inline_query_result_video import InlineQueryResultVideo`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultvideo)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
