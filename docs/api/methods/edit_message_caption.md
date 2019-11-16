# editMessageCaption

## Description

Use this method to edit captions of messages. On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Optional[Union[int, str]]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the message to edit |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |
| `caption` | `#!python3 Optional[str]` | Optional. New caption of the message |
| `parse_mode` | `#!python3 Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for an inline keyboard. |



## Response

Type: `#!python3 Union[Message, bool]`

Description: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.


## Usage


### As bot method bot

```python3
result: Union[Message, bool] = await bot.edit_message_caption(...)
```

### Method as object

Imports:

- `from aiogram.types import EditMessageCaption`
- `from aiogram.api.types import EditMessageCaption`
- `from aiogram.api.types.edit_message_caption import EditMessageCaption`

#### As reply into Webhook
```python3
return EditMessageCaption(...)
```

#### With specific bot
```python3
result: Union[Message, bool] = await bot.emit(EditMessageCaption(...))
```

#### In handlers with current bot
```python3
result: Union[Message, bool] = await EditMessageCaption(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#editmessagecaption)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
