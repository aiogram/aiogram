# deleteChatPhoto

## Description

Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.delete_chat_photo(...)
```

### Method as object

Imports:

- `from aiogram.methods import DeleteChatPhoto`
- `from aiogram.api.methods import DeleteChatPhoto`
- `from aiogram.api.methods.delete_chat_photo import DeleteChatPhoto`

#### As reply into Webhook
```python3
return DeleteChatPhoto(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(DeleteChatPhoto(...))
```

#### In handlers with current bot
```python3
result: bool = await DeleteChatPhoto(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#deletechatphoto)
