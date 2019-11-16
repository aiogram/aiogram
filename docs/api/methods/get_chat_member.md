# getChatMember

## Description

Use this method to get information about a member of a chat. Returns a ChatMember object on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername) |
| `user_id` | `#!python3 int` | Unique identifier of the target user |



## Response

Type: `#!python3 ChatMember`

Description: Returns a ChatMember object on success.


## Usage


### As bot method bot

```python3
result: ChatMember = await bot.get_chat_member(...)
```

### Method as object

Imports:

- `from aiogram.types import GetChatMember`
- `from aiogram.api.types import GetChatMember`
- `from aiogram.api.types.get_chat_member import GetChatMember`


#### With specific bot
```python3
result: ChatMember = await bot.emit(GetChatMember(...))
```

#### In handlers with current bot
```python3
result: ChatMember = await GetChatMember(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getchatmember)
- [aiogram.types.ChatMember](../types/chat_member.md)
