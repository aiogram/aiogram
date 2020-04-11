# sendDocument

## Description

Use this method to send general files. On success, the sent Message is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `document` | `#!python3 Union[InputFile, str]` | File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. |
| `thumb` | `#!python3 Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `caption` | `#!python3 Optional[str]` | Optional. Document caption (may also be used when resending documents by file_id), 0-1024 characters after entities parsing |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage

### As bot method

```python3
result: Message = await bot.send_document(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendDocument`
- `from aiogram.api.methods import SendDocument`
- `from aiogram.api.methods.send_document import SendDocument`

#### In handlers with current bot
```python3
result: Message = await SendDocument(...)
```

#### With specific bot
```python3
result: Message = await bot(SendDocument(...))
```
#### As reply into Webhook in handler
```python3
return SendDocument(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#senddocument)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [How to upload file?](../sending_files.md)
