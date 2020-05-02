# sendMessage

## Description

Use this method to send text messages. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `text` | `#!python3 str` | Text of the message to be sent, 1-4096 characters after entities parsing |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Mode for parsing entities in the message text. See formatting options for more details. |
| `disable_web_page_preview` | `#!python3 Optional[bool]` | Optional. Disables link previews for links in this message |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage

### As bot method

```python3
result: Message = await bot.send_message(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendMessage`
- `from aiogram.api.methods import SendMessage`
- `from aiogram.api.methods.send_message import SendMessage`

#### In handlers with current bot
```python3
result: Message = await SendMessage(...)
```

#### With specific bot
```python3
result: Message = await bot(SendMessage(...))
```
#### As reply into Webhook in handler
```python3
return SendMessage(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendmessage)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
