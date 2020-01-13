# setStickerPositionInSet

## Description

Use this method to move a sticker in a set created by the bot to a specific position . Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `sticker` | `#!python3 str` | File identifier of the sticker |
| `position` | `#!python3 int` | New sticker position in the set, zero-based |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_sticker_position_in_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetStickerPositionInSet`
- `from aiogram.api.methods import SetStickerPositionInSet`
- `from aiogram.api.methods.set_sticker_position_in_set import SetStickerPositionInSet`

#### In handlers with current bot
```python3
result: bool = await SetStickerPositionInSet(...)
```

#### With specific bot
```python3
result: bool = await bot(SetStickerPositionInSet(...))
```
#### As reply into Webhook in handler
```python3
return SetStickerPositionInSet(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setstickerpositioninset)
