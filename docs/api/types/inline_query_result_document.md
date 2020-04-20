# InlineQueryResultDocument

## Description

Represents a link to a file. By default, this file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the file. Currently, only .PDF and .ZIP files can be sent using this method.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be document |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `title` | `#!python str` | Title for the result |
| `document_url` | `#!python str` | A valid URL for the file |
| `mime_type` | `#!python str` | Mime type of the content of the file, either 'application/pdf' or 'application/zip' |
| `caption` | `#!python Optional[str]` | Optional. Caption of the document to be sent, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `description` | `#!python Optional[str]` | Optional. Short description of the result |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the file |
| `thumb_url` | `#!python Optional[str]` | Optional. URL of the thumbnail (jpeg only) for the file |
| `thumb_width` | `#!python Optional[int]` | Optional. Thumbnail width |
| `thumb_height` | `#!python Optional[int]` | Optional. Thumbnail height |



## Location

- `from aiogram.types import InlineQueryResultDocument`
- `from aiogram.api.types import InlineQueryResultDocument`
- `from aiogram.api.types.inline_query_result_document import InlineQueryResultDocument`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultdocument)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
