# InlineQueryResultAudio

## Description

Represents a link to an MP3 audio file. By default, this audio file will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the audio.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be audio |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `audio_url` | `#!python str` | A valid URL for the audio file |
| `title` | `#!python str` | Title |
| `caption` | `#!python Optional[str]` | Optional. Caption, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Mode for parsing entities in the audio caption. See formatting options for more details. |
| `performer` | `#!python Optional[str]` | Optional. Performer |
| `audio_duration` | `#!python Optional[int]` | Optional. Audio duration in seconds |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the audio |



## Location

- `from aiogram.types import InlineQueryResultAudio`
- `from aiogram.api.types import InlineQueryResultAudio`
- `from aiogram.api.types.inline_query_result_audio import InlineQueryResultAudio`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultaudio)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
