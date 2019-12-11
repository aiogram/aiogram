# sendLocation

## Description

Use this method to send point on the map. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `latitude` | `#!python3 float` | Latitude of the location |
| `longitude` | `#!python3 float` | Longitude of the location |
| `live_period` | `#!python3 Optional[int]` | Optional. Period in seconds for which the location will be updated (see Live Locations, should be between 60 and 86400. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_location(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendLocation`
- `from aiogram.api.methods import SendLocation`
- `from aiogram.api.methods.send_location import SendLocation`

#### As reply into Webhook
```python3
return SendLocation(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendLocation(...))
```

#### In handlers with current bot
```python3
result: Message = await SendLocation(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendlocation)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
