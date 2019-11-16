# sendAnimation

## Description

Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent Message is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `animation` | `#!python3 Union[InputFile, str]` | Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. |
| `duration` | `#!python3 Optional[int]` | Optional. Duration of sent animation in seconds |
| `width` | `#!python3 Optional[int]` | Optional. Animation width |
| `height` | `#!python3 Optional[int]` | Optional. Animation height |
| `thumb` | `#!python3 Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `caption` | `#!python3 Optional[str]` | Optional. Animation caption (may also be used when resending animation by file_id), 0-1024 characters |
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
result: Message = await bot.send_animation(...)
```

### Method as object

Imports:

- `from aiogram.types import SendAnimation`
- `from aiogram.api.types import SendAnimation`
- `from aiogram.api.types.send_animation import SendAnimation`

#### As reply into Webhook
```python3
return SendAnimation(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendAnimation(...))
```

#### In handlers with current bot
```python3
result: Message = await SendAnimation(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendanimation)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
