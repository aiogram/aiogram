# InlineQueryResultGif

## Description

Represents a link to an animated GIF file. By default, this animated GIF file will be sent by the user with optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the animation.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be gif |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `gif_url` | `#!python str` | A valid URL for the GIF file. File size must not exceed 1MB |
| `thumb_url` | `#!python str` | URL of the static thumbnail for the result (jpeg or gif) |
| `gif_width` | `#!python Optional[int]` | Optional. Width of the GIF |
| `gif_height` | `#!python Optional[int]` | Optional. Height of the GIF |
| `gif_duration` | `#!python Optional[int]` | Optional. Duration of the GIF |
| `title` | `#!python Optional[str]` | Optional. Title for the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the GIF file to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the GIF animation |



## Location

- `from aiogram.types import InlineQueryResultGif`
- `from aiogram.api.types import InlineQueryResultGif`
- `from aiogram.api.types.inline_query_result_gif import InlineQueryResultGif`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultgif)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
