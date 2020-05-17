# addStickerToSet

## Description

Use this method to add a new sticker to a set created by the bot. You must use exactly one of the fields png_sticker or tgs_sticker. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | User identifier of sticker set owner |
| `name` | `#!python3 str` | Sticker set name |
| `emojis` | `#!python3 str` | One or more emoji corresponding to the sticker |
| `png_sticker` | `#!python3 Optional[Union[InputFile, str]]` | Optional. PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. |
| `tgs_sticker` | `#!python3 Optional[InputFile]` | Optional. TGS animation with the sticker, uploaded using multipart/form-data. See https://core.telegram.org/animated_stickers#technical-requirements for technical requirements |
| `mask_position` | `#!python3 Optional[MaskPosition]` | Optional. A JSON-serialized object for position where the mask should be placed on faces |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.add_sticker_to_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import AddStickerToSet`
- `from aiogram.api.methods import AddStickerToSet`
- `from aiogram.api.methods.add_sticker_to_set import AddStickerToSet`

#### In handlers with current bot
```python3
result: bool = await AddStickerToSet(...)
```

#### With specific bot
```python3
result: bool = await bot(AddStickerToSet(...))
```
#### As reply into Webhook in handler
```python3
return AddStickerToSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#addstickertoset)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.MaskPosition](../types/mask_position.md)
- [How to upload file?](../upload_file.md)
