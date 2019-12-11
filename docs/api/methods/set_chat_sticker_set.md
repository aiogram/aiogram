# setChatStickerSet

## Description

Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername) |
| `sticker_set_name` | `#!python3 str` | Name of the sticker set to be set as the group sticker set |



## Response

Type: `#!python3 bool`

Description: Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_chat_sticker_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetChatStickerSet`
- `from aiogram.api.methods import SetChatStickerSet`
- `from aiogram.api.methods.set_chat_sticker_set import SetChatStickerSet`

#### As reply into Webhook
```python3
return SetChatStickerSet(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(SetChatStickerSet(...))
```

#### In handlers with current bot
```python3
result: bool = await SetChatStickerSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setchatstickerset)
