# unpinChatMessage

## Description

Use this method to unpin a message in a group, a supergroup, or a channel. The bot must be an administrator in the chat for this to work and must have the ‘can_pin_messages’ admin right in the supergroup or ‘can_edit_messages’ admin right in the channel. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.unpin_chat_message(...)
```

### Method as object

Imports:

- `from aiogram.methods import UnpinChatMessage`
- `from aiogram.api.methods import UnpinChatMessage`
- `from aiogram.api.methods.unpin_chat_message import UnpinChatMessage`

#### In handlers with current bot
```python3
result: bool = await UnpinChatMessage(...)
```

#### With specific bot
```python3
result: bool = await bot(UnpinChatMessage(...))
```
#### As reply into Webhook in handler
```python3
return UnpinChatMessage(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#unpinchatmessage)
