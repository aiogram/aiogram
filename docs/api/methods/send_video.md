# sendVideo

## Description

Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as Document). On success, the sent Message is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `video` | `#!python3 Union[InputFile, str]` | Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. |
| `duration` | `#!python3 Optional[int]` | Optional. Duration of sent video in seconds |
| `width` | `#!python3 Optional[int]` | Optional. Video width |
| `height` | `#!python3 Optional[int]` | Optional. Video height |
| `thumb` | `#!python3 Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `caption` | `#!python3 Optional[str]` | Optional. Video caption (may also be used when resending videos by file_id), 0-1024 characters |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `supports_streaming` | `#!python3 Optional[bool]` | Optional. Pass True, if the uploaded video is suitable for streaming |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_video(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendVideo`
- `from aiogram.api.methods import SendVideo`
- `from aiogram.api.methods.send_video import SendVideo`

#### In handlers with current bot
```python3
result: Message = await SendVideo(...)
```

#### With specific bot
```python3
result: Message = await bot(SendVideo(...))
```
#### As reply into Webhook in handler
```python3
return SendVideo(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendvideo)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [How to upload file?](../sending_files.md)
