# InlineQueryResultArticle

## Description

Represents a link to an article or web page.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be article |
| `id` | `#!python str` | Unique identifier for this result, 1-64 Bytes |
| `title` | `#!python str` | Title of the result |
| `input_message_content` | `#!python InputMessageContent` | Content of the message to be sent |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `url` | `#!python Optional[str]` | Optional. URL of the result |
| `hide_url` | `#!python Optional[bool]` | Optional. Pass True, if you don't want the URL to be shown in the message |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `thumb_url` | `#!python Optional[str]` | Optional. Url of the thumbnail for the result |
| `thumb_width` | `#!python Optional[int]` | Optional. Thumbnail width |
| `thumb_height` | `#!python Optional[int]` | Optional. Thumbnail height |



## Location

- `from aiogram.types import InlineQueryResultArticle`
- `from aiogram.api.types import InlineQueryResultArticle`
- `from aiogram.api.types.inline_query_result_article import InlineQueryResultArticle`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultarticle)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
