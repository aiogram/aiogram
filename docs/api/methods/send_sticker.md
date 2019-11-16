# sendSticker

## Description

Use this method to send static .WEBP or animated .TGS stickers. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `sticker` | `#!python3 Union[InputFile, str]` | Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .webp file from the Internet, or upload a new one using multipart/form-data. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_sticker(...)
```

### Method as object

Imports:

- `from aiogram.types import SendSticker`
- `from aiogram.api.types import SendSticker`
- `from aiogram.api.types.send_sticker import SendSticker`

#### As reply into Webhook
```python3
return SendSticker(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendSticker(...))
```

#### In handlers with current bot
```python3
result: Message = await SendSticker(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendsticker)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
