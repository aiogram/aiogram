# deleteStickerFromSet

## Description

Use this method to delete a sticker from a set created by the bot. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `sticker` | `#!python3 str` | File identifier of the sticker |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.delete_sticker_from_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import DeleteStickerFromSet`
- `from aiogram.api.methods import DeleteStickerFromSet`
- `from aiogram.api.methods.delete_sticker_from_set import DeleteStickerFromSet`

#### As reply into Webhook
```python3
return DeleteStickerFromSet(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(DeleteStickerFromSet(...))
```

#### In handlers with current bot
```python3
result: bool = await DeleteStickerFromSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#deletestickerfromset)
