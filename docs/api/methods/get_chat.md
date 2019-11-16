# getChat

## Description

Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername) |



## Response

Type: `#!python3 Chat`

Description: Returns a Chat object on success.


## Usage


### As bot method bot

```python3
result: Chat = await bot.get_chat(...)
```

### Method as object

Imports:

- `from aiogram.types import GetChat`
- `from aiogram.api.types import GetChat`
- `from aiogram.api.types.get_chat import GetChat`


#### With specific bot
```python3
result: Chat = await bot.emit(GetChat(...))
```

#### In handlers with current bot
```python3
result: Chat = await GetChat(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getchat)
- [aiogram.types.Chat](../types/chat.md)
