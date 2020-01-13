# getChatMembersCount

## Description

Use this method to get the number of members in a chat. Returns Int on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername) |



## Response

Type: `#!python3 int`

Description: Returns Int on success.


## Usage


### As bot method bot

```python3
result: int = await bot.get_chat_members_count(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetChatMembersCount`
- `from aiogram.api.methods import GetChatMembersCount`
- `from aiogram.api.methods.get_chat_members_count import GetChatMembersCount`

#### In handlers with current bot
```python3
result: int = await GetChatMembersCount(...)
```

#### With specific bot
```python3
result: int = await bot(GetChatMembersCount(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getchatmemberscount)
