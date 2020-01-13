# InlineQueryResultVenue

## Description

Represents a venue. By default, the venue will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the venue.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be venue |
| `id` | `#!python str` | Unique identifier for this result, 1-64 Bytes |
| `latitude` | `#!python float` | Latitude of the venue location in degrees |
| `longitude` | `#!python float` | Longitude of the venue location in degrees |
| `title` | `#!python str` | Title of the venue |
| `address` | `#!python str` | Address of the venue |
| `foursquare_id` | `#!python Optional[str]` | Optional. Foursquare identifier of the venue if known |
| `foursquare_type` | `#!python Optional[str]` | Optional. Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.) |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the venue |
| `thumb_url` | `#!python Optional[str]` | Optional. Url of the thumbnail for the result |
| `thumb_width` | `#!python Optional[int]` | Optional. Thumbnail width |
| `thumb_height` | `#!python Optional[int]` | Optional. Thumbnail height |



## Location

- `from aiogram.types import InlineQueryResultVenue`
- `from aiogram.api.types import InlineQueryResultVenue`
- `from aiogram.api.types.inline_query_result_venue import InlineQueryResultVenue`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultvenue)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
