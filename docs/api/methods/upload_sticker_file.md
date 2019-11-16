# uploadStickerFile

## Description

Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet methods (can be used multiple times). Returns the uploaded File on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | User identifier of sticker file owner |
| `png_sticker` | `#!python3 InputFile` | Png image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. |



## Response

Type: `#!python3 File`

Description: Returns the uploaded File on success.


## Usage


### As bot method bot

```python3
result: File = await bot.upload_sticker_file(...)
```

### Method as object

Imports:

- `from aiogram.types import UploadStickerFile`
- `from aiogram.api.types import UploadStickerFile`
- `from aiogram.api.types.upload_sticker_file import UploadStickerFile`


#### With specific bot
```python3
result: File = await bot.emit(UploadStickerFile(...))
```

#### In handlers with current bot
```python3
result: File = await UploadStickerFile(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#uploadstickerfile)
- [aiogram.types.InputFile](../types/input_file.md)
- [aiogram.types.File](../types/file.md)
