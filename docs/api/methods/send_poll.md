# sendPoll

## Description

Use this method to send a native poll. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `question` | `#!python3 str` | Poll question, 1-255 characters |
| `options` | `#!python3 List[str]` | A JSON-serialized list of answer options, 2-10 strings 1-100 characters each |
| `is_anonymous` | `#!python3 Optional[bool]` | Optional. True, if the poll needs to be anonymous, defaults to True |
| `type` | `#!python3 Optional[str]` | Optional. Poll type, 'quiz' or 'regular', defaults to 'regular' |
| `allows_multiple_answers` | `#!python3 Optional[bool]` | Optional. True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to False |
| `correct_option_id` | `#!python3 Optional[int]` | Optional. 0-based identifier of the correct answer option, required for polls in quiz mode |
| `is_closed` | `#!python3 Optional[bool]` | Optional. Pass True, if the poll needs to be immediately closed. This can be useful for poll preview. |
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

- `from aiogram.methods import SendPoll`
- `from aiogram.api.methods import SendPoll`
- `from aiogram.api.methods.send_poll import SendPoll`

#### In handlers with current bot
```python3
result: Message = await SendPoll(...)
```

#### With specific bot
```python3
result: Message = await bot(SendPoll(...))
```
#### As reply into Webhook in handler
```python3
return SendPoll(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendpoll)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
