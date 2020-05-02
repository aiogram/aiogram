# sendDice

## Description

Use this method to send a dice, which will have a random value from 1 to 6. On success, the sent Message is returned. (Yes, we're aware of the 'proper' singular of die. But it's awkward, and we decided to help it change. One dice at a time!)


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `emoji` | `#!python3 Optional[str]` | Optional. Emoji on which the dice throw animation is based. Currently, must be one of '' or ''. Defauts to '' |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage

### As bot method

```python3
result: Message = await bot.send_dice(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendDice`
- `from aiogram.api.methods import SendDice`
- `from aiogram.api.methods.send_dice import SendDice`

#### In handlers with current bot
```python3
result: Message = await SendDice(...)
```

#### With specific bot
```python3
result: Message = await bot(SendDice(...))
```
#### As reply into Webhook in handler
```python3
return SendDice(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#senddice)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
