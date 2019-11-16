# sendContact

## Description

Use this method to send phone contacts. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `phone_number` | `#!python3 str` | Contact's phone number |
| `first_name` | `#!python3 str` | Contact's first name |
| `last_name` | `#!python3 Optional[str]` | Optional. Contact's last name |
| `vcard` | `#!python3 Optional[str]` | Optional. Additional data about the contact in the form of a vCard, 0-2048 bytes |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_contact(...)
```

### Method as object

Imports:

- `from aiogram.types import SendContact`
- `from aiogram.api.types import SendContact`
- `from aiogram.api.types.send_contact import SendContact`

#### As reply into Webhook
```python3
return SendContact(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendContact(...))
```

#### In handlers with current bot
```python3
result: Message = await SendContact(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendcontact)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
