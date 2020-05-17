# setStickerSetThumb

## Description

Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `name` | `#!python3 str` | Sticker set name |
| `user_id` | `#!python3 int` | User identifier of the sticker set owner |
| `thumb` | `#!python3 Optional[Union[InputFile, str]]` | Optional. A PNG image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a TGS animation with the thumbnail up to 32 kilobytes in size; see https://core.telegram.org/animated_stickers#technical-requirements for animated sticker technical requirements. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.. Animated sticker set thumbnail can't be uploaded via HTTP URL. |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.set_sticker_set_thumb(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetStickerSetThumb`
- `from aiogram.api.methods import SetStickerSetThumb`
- `from aiogram.api.methods.set_sticker_set_thumb import SetStickerSetThumb`

#### In handlers with current bot
```python3
result: bool = await SetStickerSetThumb(...)
```

#### With specific bot
```python3
result: bool = await bot(SetStickerSetThumb(...))
```
#### As reply into Webhook in handler
```python3
return SetStickerSetThumb(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setstickersetthumb)
- [aiogram.types.InputFile](../types/input_file.md)
- [How to upload file?](../upload_file.md)
