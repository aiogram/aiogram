# editMessageLiveLocation

## Description

Use this method to edit live location messages. A location can be edited until its live_period expires or editing is explicitly disabled by a call to stopMessageLiveLocation. On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `latitude` | `#!python3 float` | Latitude of new location |
| `longitude` | `#!python3 float` | Longitude of new location |
| `chat_id` | `#!python3 Optional[Union[int, str]]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the message to edit |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for a new inline keyboard. |



## Response

Type: `#!python3 Union[Message, bool]`

Description: On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.


## Usage


### As bot method bot

```python3
result: Union[Message, bool] = await bot.edit_message_live_location(...)
```

### Method as object

Imports:

- `from aiogram.types import EditMessageLiveLocation`
- `from aiogram.api.types import EditMessageLiveLocation`
- `from aiogram.api.types.edit_message_live_location import EditMessageLiveLocation`

#### As reply into Webhook
```python3
return EditMessageLiveLocation(...)
```

#### With specific bot
```python3
result: Union[Message, bool] = await bot.emit(EditMessageLiveLocation(...))
```

#### In handlers with current bot
```python3
result: Union[Message, bool] = await EditMessageLiveLocation(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#editmessagelivelocation)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
