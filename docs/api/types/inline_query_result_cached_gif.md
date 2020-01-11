# InlineQueryResultCachedGif

## Description

Represents a link to an animated GIF file stored on the Telegram servers. By default, this animated GIF file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with specified content instead of the animation.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be gif |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `gif_file_id` | `#!python str` | A valid file identifier for the GIF file |
| `title` | `#!python Optional[str]` | Optional. Title for the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the GIF file to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the GIF animation |



## Location

- `from aiogram.types import InlineQueryResultCachedGif`
- `from aiogram.api.types import InlineQueryResultCachedGif`
- `from aiogram.api.types.inline_query_result_cached_gif import InlineQueryResultCachedGif`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcachedgif)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
