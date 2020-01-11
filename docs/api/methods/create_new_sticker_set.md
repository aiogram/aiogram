# createNewStickerSet

## Description

Use this method to create new sticker set owned by a user. The bot will be able to edit the created sticker set. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | User identifier of created sticker set owner |
| `name` | `#!python3 str` | Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals). Can contain only english letters, digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in '_by_<bot username>'. <bot_username> is case insensitive. 1-64 characters. |
| `title` | `#!python3 str` | Sticker set title, 1-64 characters |
| `png_sticker` | `#!python3 Union[InputFile, str]` | Png image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. |
| `emojis` | `#!python3 str` | One or more emoji corresponding to the sticker |
| `contains_masks` | `#!python3 Optional[bool]` | Optional. Pass True, if a set of mask stickers should be created |
| `mask_position` | `#!python3 Optional[MaskPosition]` | Optional. A JSON-serialized object for position where the mask should be placed on faces |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.create_new_sticker_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import CreateNewStickerSet`
- `from aiogram.api.methods import CreateNewStickerSet`
- `from aiogram.api.methods.create_new_sticker_set import CreateNewStickerSet`

#### As reply into Webhook
```python3
return CreateNewStickerSet(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(CreateNewStickerSet(...))
```

#### In handlers with current bot
```python3
result: bool = await CreateNewStickerSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#createnewstickerset)
- [aiogram.types.MaskPosition](../types/mask_position.md)
- [aiogram.types.InputFile](../types/input_file.md)
