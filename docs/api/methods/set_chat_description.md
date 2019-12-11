# setChatDescription

## Description

Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `description` | `#!python3 Optional[str]` | Optional. New chat description, 0-255 characters |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_chat_description(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetChatDescription`
- `from aiogram.api.methods import SetChatDescription`
- `from aiogram.api.methods.set_chat_description import SetChatDescription`

#### As reply into Webhook
```python3
return SetChatDescription(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(SetChatDescription(...))
```

#### In handlers with current bot
```python3
result: bool = await SetChatDescription(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setchatdescription)
