# InlineQueryResultVoice

## Description

Represents a link to a voice recording in an .OGG container encoded with OPUS. By default, this voice recording will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the the voice message.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be voice |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `voice_url` | `#!python str` | A valid URL for the voice recording |
| `title` | `#!python str` | Recording title |
| `caption` | `#!python Optional[str]` | Optional. Caption, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Mode for parsing entities in the voice message caption. See formatting options for more details. |
| `voice_duration` | `#!python Optional[int]` | Optional. Recording duration in seconds |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the voice recording |



## Location

- `from aiogram.types import InlineQueryResultVoice`
- `from aiogram.api.types import InlineQueryResultVoice`
- `from aiogram.api.types.inline_query_result_voice import InlineQueryResultVoice`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultvoice)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
