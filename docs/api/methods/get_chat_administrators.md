# getChatAdministrators

## Description

Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername) |



## Response

Type: `#!python3 List[ChatMember]`

Description: On success, returns an Array of ChatMember objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.


## Usage


### As bot method bot

```python3
result: List[ChatMember] = await bot.get_chat_administrators(...)
```

### Method as object

Imports:

- `from aiogram.types import GetChatAdministrators`
- `from aiogram.api.types import GetChatAdministrators`
- `from aiogram.api.types.get_chat_administrators import GetChatAdministrators`


#### With specific bot
```python3
result: List[ChatMember] = await bot.emit(GetChatAdministrators(...))
```

#### In handlers with current bot
```python3
result: List[ChatMember] = await GetChatAdministrators(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getchatadministrators)
- [aiogram.types.ChatMember](../types/chat_member.md)
