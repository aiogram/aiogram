# InlineQueryResultPhoto

## Description

Represents a link to a photo. By default, this photo will be sent by the user with optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the photo.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be photo |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `photo_url` | `#!python str` | A valid URL of the photo. Photo must be in jpeg format. Photo size must not exceed 5MB |
| `thumb_url` | `#!python str` | URL of the thumbnail for the photo |
| `photo_width` | `#!python Optional[int]` | Optional. Width of the photo |
| `photo_height` | `#!python Optional[int]` | Optional. Height of the photo |
| `title` | `#!python Optional[str]` | Optional. Title for the result |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the photo to be sent, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Mode for parsing entities in the photo caption. See formatting options for more details. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the photo |



## Location

- `from aiogram.types import InlineQueryResultPhoto`
- `from aiogram.api.types import InlineQueryResultPhoto`
- `from aiogram.api.types.inline_query_result_photo import InlineQueryResultPhoto`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultphoto)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
