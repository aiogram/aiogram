# InlineQueryResultCachedSticker

## Description

Represents a link to a sticker stored on the Telegram servers. By default, this sticker will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the sticker.

Note: This will only work in Telegram versions released after 9 April, 2016 for static stickers and after 06 July, 2019 for animated stickers. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be sticker |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `sticker_file_id` | `#!python str` | A valid file identifier of the sticker |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the sticker |



## Location

- `from aiogram.types import InlineQueryResultCachedSticker`
- `from aiogram.api.types import InlineQueryResultCachedSticker`
- `from aiogram.api.types.inline_query_result_cached_sticker import InlineQueryResultCachedSticker`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcachedsticker)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
