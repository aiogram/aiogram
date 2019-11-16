# InlineQueryResultCachedPhoto

## Description

Represents a link to a photo stored on the Telegram servers. By default, this photo will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the photo.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be photo |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `photo_file_id` | `#!python str` | A valid file identifier of the photo |
| `title` | `#!python Optional[str]` | Optional. Title for the result |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the photo to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the photo |



## Location

- `from aiogram.types import InlineQueryResultCachedPhoto`
- `from aiogram.api.types import InlineQueryResultCachedPhoto`
- `from aiogram.api.types.inline_query_result_cached_photo import InlineQueryResultCachedPhoto`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcachedphoto)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
