# createNewStickerSet

## Description

Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You must use exactly one of the fields png_sticker or tgs_sticker. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | User identifier of created sticker set owner |
| `name` | `#!python3 str` | Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals). Can contain only english letters, digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in '_by_<bot username>'. <bot_username> is case insensitive. 1-64 characters. |
| `title` | `#!python3 str` | Sticker set title, 1-64 characters |
| `emojis` | `#!python3 str` | One or more emoji corresponding to the sticker |
| `png_sticker` | `#!python3 Optional[Union[InputFile, str]]` | Optional. PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. |
| `tgs_sticker` | `#!python3 Optional[InputFile]` | Optional. TGS animation with the sticker, uploaded using multipart/form-data. See https://core.telegram.org/animated_stickers#technical-requirements for technical requirements |
| `contains_masks` | `#!python3 Optional[bool]` | Optional. Pass True, if a set of mask stickers should be created |
| `mask_position` | `#!python3 Optional[MaskPosition]` | Optional. A JSON-serialized object for position where the mask should be placed on faces |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.create_new_sticker_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import CreateNewStickerSet`
- `from aiogram.api.methods import CreateNewStickerSet`
- `from aiogram.api.methods.create_new_sticker_set import CreateNewStickerSet`

#### In handlers with current bot
```python3
result: bool = await CreateNewStickerSet(...)
```

#### With specific bot
```python3
result: bool = await bot(CreateNewStickerSet(...))
```
#### As reply into Webhook in handler
```python3
return CreateNewStickerSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#createnewstickerset)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.MaskPosition](../types/mask_position.md)
- [How to upload file?](../sending_files.md)
