# sendVoice

## Description

Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .ogg file encoded with OPUS (other formats may be sent as Audio or Document). On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `voice` | `#!python3 Union[InputFile, str]` | Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. |
| `caption` | `#!python3 Optional[str]` | Optional. Voice message caption, 0-1024 characters |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `duration` | `#!python3 Optional[int]` | Optional. Duration of the voice message in seconds |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_voice(...)
```

### Method as object

Imports:

- `from aiogram.types import SendVoice`
- `from aiogram.api.types import SendVoice`
- `from aiogram.api.types.send_voice import SendVoice`

#### As reply into Webhook
```python3
return SendVoice(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendVoice(...))
```

#### In handlers with current bot
```python3
result: Message = await SendVoice(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendvoice)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
