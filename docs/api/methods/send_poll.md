# sendPoll

## Description

Use this method to send a native poll. A native poll can't be sent to a private chat. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername). A native poll can't be sent to a private chat. |
| `question` | `#!python3 str` | Poll question, 1-255 characters |
| `options` | `#!python3 List[str]` | List of answer options, 2-10 strings 1-100 characters each |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_poll(...)
```

### Method as object

Imports:

- `from aiogram.types import SendPoll`
- `from aiogram.api.types import SendPoll`
- `from aiogram.api.types.send_poll import SendPoll`

#### As reply into Webhook
```python3
return SendPoll(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendPoll(...))
```

#### In handlers with current bot
```python3
result: Message = await SendPoll(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendpoll)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
