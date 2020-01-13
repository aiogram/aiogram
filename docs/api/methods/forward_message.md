# forwardMessage

## Description

Use this method to forward messages of any kind. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `from_chat_id` | `#!python3 Union[int, str]` | Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername) |
| `message_id` | `#!python3 int` | Message identifier in the chat specified in from_chat_id |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.forward_message(...)
```

### Method as object

Imports:

- `from aiogram.methods import ForwardMessage`
- `from aiogram.api.methods import ForwardMessage`
- `from aiogram.api.methods.forward_message import ForwardMessage`

#### In handlers with current bot
```python3
result: Message = await ForwardMessage(...)
```

#### With specific bot
```python3
result: Message = await bot(ForwardMessage(...))
```
#### As reply into Webhook in handler
```python3
return ForwardMessage(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#forwardmessage)
- [aiogram.types.Message](../types/message.md)
