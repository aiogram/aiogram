# deleteChatStickerSet

## Description

Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername) |



## Response

Type: `#!python3 bool`

Description: Use the field can_set_sticker_set optionally returned in getChat requests to check if the bot can use this method. Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.delete_chat_sticker_set(...)
```

### Method as object

Imports:

- `from aiogram.methods import DeleteChatStickerSet`
- `from aiogram.api.methods import DeleteChatStickerSet`
- `from aiogram.api.methods.delete_chat_sticker_set import DeleteChatStickerSet`

#### As reply into Webhook
```python3
return DeleteChatStickerSet(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(DeleteChatStickerSet(...))
```

#### In handlers with current bot
```python3
result: bool = await DeleteChatStickerSet(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#deletechatstickerset)
