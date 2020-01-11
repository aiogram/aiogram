# InlineQueryResultCachedDocument

## Description

Represents a link to a file stored on the Telegram servers. By default, this file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the file.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be document |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `title` | `#!python str` | Title for the result |
| `document_file_id` | `#!python str` | A valid file identifier for the file |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `caption` | `#!python Optional[str]` | Optional. Caption of the document to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the file |



## Location

- `from aiogram.types import InlineQueryResultCachedDocument`
- `from aiogram.api.types import InlineQueryResultCachedDocument`
- `from aiogram.api.types.inline_query_result_cached_document import InlineQueryResultCachedDocument`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcacheddocument)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
