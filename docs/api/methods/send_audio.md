# sendAudio

## Description

Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent Message is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.

For sending voice messages, use the sendVoice method instead.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `audio` | `#!python3 Union[InputFile, str]` | Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. |
| `caption` | `#!python3 Optional[str]` | Optional. Audio caption, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Mode for parsing entities in the audio caption. See formatting options for more details. |
| `duration` | `#!python3 Optional[int]` | Optional. Duration of the audio in seconds |
| `performer` | `#!python3 Optional[str]` | Optional. Performer |
| `title` | `#!python3 Optional[str]` | Optional. Track name |
| `thumb` | `#!python3 Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage

### As bot method

```python3
result: Message = await bot.send_audio(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendAudio`
- `from aiogram.api.methods import SendAudio`
- `from aiogram.api.methods.send_audio import SendAudio`

#### In handlers with current bot
```python3
result: Message = await SendAudio(...)
```

#### With specific bot
```python3
result: Message = await bot(SendAudio(...))
```
#### As reply into Webhook in handler
```python3
return SendAudio(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendaudio)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [How to upload file?](../upload_file.md)
