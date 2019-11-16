# sendPhoto

## Description

Use this method to send photos. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `photo` | `#!python3 Union[InputFile, str]` | Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. |
| `caption` | `#!python3 Optional[str]` | Optional. Photo caption (may also be used when resending photos by file_id), 0-1024 characters |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_photo(...)
```

### Method as object

Imports:

- `from aiogram.types import SendPhoto`
- `from aiogram.api.types import SendPhoto`
- `from aiogram.api.types.send_photo import SendPhoto`

#### As reply into Webhook
```python3
return SendPhoto(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendPhoto(...))
```

#### In handlers with current bot
```python3
result: Message = await SendPhoto(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendphoto)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
