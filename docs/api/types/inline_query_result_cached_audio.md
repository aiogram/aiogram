# InlineQueryResultCachedAudio

## Description

Represents a link to an MP3 audio file stored on the Telegram servers. By default, this audio file will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the audio.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be audio |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `audio_file_id` | `#!python str` | A valid file identifier for the audio file |
| `caption` | `#!python Optional[str]` | Optional. Caption, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the audio |



## Location

- `from aiogram.types import InlineQueryResultCachedAudio`
- `from aiogram.api.types import InlineQueryResultCachedAudio`
- `from aiogram.api.types.inline_query_result_cached_audio import InlineQueryResultCachedAudio`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcachedaudio)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
