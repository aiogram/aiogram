# getStickerSet

## Description

Use this method to get a sticker set. On success, a StickerSet object is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `name` | `#!python3 str` | Name of the sticker set |



## Response

Type: `#!python3 StickerSet`

Description: On success, a StickerSet object is returned.


## Usage


### As bot method bot

```python3
result: StickerSet = await bot.get_sticker_set(...)
```

### Method as object

Imports:

- `from aiogram.types import GetStickerSet`
- `from aiogram.api.types import GetStickerSet`
- `from aiogram.api.types.get_sticker_set import GetStickerSet`


#### With specific bot
```python3
result: StickerSet = await bot.emit(GetStickerSet(...))
```

#### In handlers with current bot
```python3
result: StickerSet = await GetStickerSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getstickerset)
- [aiogram.types.StickerSet](../types/sticker_set.md)
