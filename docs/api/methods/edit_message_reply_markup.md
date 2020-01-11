# editMessageReplyMarkup

## Description

Use this method to edit only the reply markup of messages. On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Optional[Union[int, str]]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the message to edit |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for an inline keyboard. |



## Response

Type: `#!python3 Union[Message, bool]`

Description: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.


## Usage


### As bot method bot

```python3
result: Union[Message, bool] = await bot.edit_message_reply_markup(...)
```

### Method as object

Imports:

- `from aiogram.methods import EditMessageReplyMarkup`
- `from aiogram.api.methods import EditMessageReplyMarkup`
- `from aiogram.api.methods.edit_message_reply_markup import EditMessageReplyMarkup`

#### In handlers with current bot
```python3
result: Union[Message, bool] = await EditMessageReplyMarkup(...)
```

#### With specific bot
```python3
result: Union[Message, bool] = await bot(EditMessageReplyMarkup(...))
```
#### As reply into Webhook in handler
```python3
return EditMessageReplyMarkup(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#editmessagereplymarkup)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
