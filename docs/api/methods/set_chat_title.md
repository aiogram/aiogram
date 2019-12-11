# setChatTitle

## Description

Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `title` | `#!python3 str` | New chat title, 1-255 characters |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_chat_title(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetChatTitle`
- `from aiogram.api.methods import SetChatTitle`
- `from aiogram.api.methods.set_chat_title import SetChatTitle`

#### As reply into Webhook
```python3
return SetChatTitle(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(SetChatTitle(...))
```

#### In handlers with current bot
```python3
result: bool = await SetChatTitle(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setchattitle)
