# pinChatMessage

## Description

Use this method to pin a message in a group, a supergroup, or a channel. The bot must be an administrator in the chat for this to work and must have the ‘can_pin_messages’ admin right in the supergroup or ‘can_edit_messages’ admin right in the channel. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 int` | Identifier of a message to pin |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Pass True, if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels. |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.pin_chat_message(...)
```

### Method as object

Imports:

- `from aiogram.methods import PinChatMessage`
- `from aiogram.api.methods import PinChatMessage`
- `from aiogram.api.methods.pin_chat_message import PinChatMessage`

#### In handlers with current bot
```python3
result: bool = await PinChatMessage(...)
```

#### With specific bot
```python3
result: bool = await bot(PinChatMessage(...))
```
#### As reply into Webhook in handler
```python3
return PinChatMessage(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#pinchatmessage)
