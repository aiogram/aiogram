# sendVideoNote

## Description

As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `video_note` | `#!python3 Union[InputFile, str]` | Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data.. Sending video notes by a URL is currently unsupported |
| `duration` | `#!python3 Optional[int]` | Optional. Duration of sent video in seconds |
| `length` | `#!python3 Optional[int]` | Optional. Video width and height, i.e. diameter of the video message |
| `thumb` | `#!python3 Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_video_note(...)
```

### Method as object

Imports:

- `from aiogram.types import SendVideoNote`
- `from aiogram.api.types import SendVideoNote`
- `from aiogram.api.types.send_video_note import SendVideoNote`

#### As reply into Webhook
```python3
return SendVideoNote(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendVideoNote(...))
```

#### In handlers with current bot
```python3
result: Message = await SendVideoNote(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendvideonote)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
