# InlineQueryResultLocation

## Description

Represents a location on a map. By default, the location will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the location.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be location |
| `id` | `#!python str` | Unique identifier for this result, 1-64 Bytes |
| `latitude` | `#!python float` | Location latitude in degrees |
| `longitude` | `#!python float` | Location longitude in degrees |
| `title` | `#!python str` | Location title |
| `live_period` | `#!python Optional[int]` | Optional. Period in seconds for which the location can be updated, should be between 60 and 86400. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the location |
| `thumb_url` | `#!python Optional[str]` | Optional. Url of the thumbnail for the result |
| `thumb_width` | `#!python Optional[int]` | Optional. Thumbnail width |
| `thumb_height` | `#!python Optional[int]` | Optional. Thumbnail height |



## Location

- `from aiogram.types import InlineQueryResultLocation`
- `from aiogram.api.types import InlineQueryResultLocation`
- `from aiogram.api.types.inline_query_result_location import InlineQueryResultLocation`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultlocation)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
