# stopMessageLiveLocation

## Description

Use this method to stop updating a live location message before live_period expires. On success, if the message was sent by the bot, the sent Message is returned, otherwise True is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Optional[Union[int, str]]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the message with live location to stop |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for a new inline keyboard. |



## Response

Type: `#!python3 Union[Message, bool]`

Description: On success, if the message was sent by the bot, the sent Message is returned, otherwise True is returned.


## Usage


### As bot method bot

```python3
result: Union[Message, bool] = await bot.stop_message_live_location(...)
```

### Method as object

Imports:

- `from aiogram.types import StopMessageLiveLocation`
- `from aiogram.api.types import StopMessageLiveLocation`
- `from aiogram.api.types.stop_message_live_location import StopMessageLiveLocation`

#### As reply into Webhook
```python3
return StopMessageLiveLocation(...)
```

#### With specific bot
```python3
result: Union[Message, bool] = await bot.emit(StopMessageLiveLocation(...))
```

#### In handlers with current bot
```python3
result: Union[Message, bool] = await StopMessageLiveLocation(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#stopmessagelivelocation)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
