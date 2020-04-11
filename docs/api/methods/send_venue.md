# sendVenue

## Description

Use this method to send information about a venue. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `latitude` | `#!python3 float` | Latitude of the venue |
| `longitude` | `#!python3 float` | Longitude of the venue |
| `title` | `#!python3 str` | Name of the venue |
| `address` | `#!python3 str` | Address of the venue |
| `foursquare_id` | `#!python3 Optional[str]` | Optional. Foursquare identifier of the venue |
| `foursquare_type` | `#!python3 Optional[str]` | Optional. Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.) |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]]` | Optional. Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage

### As bot method

```python3
result: Message = await bot.send_venue(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendVenue`
- `from aiogram.api.methods import SendVenue`
- `from aiogram.api.methods.send_venue import SendVenue`

#### In handlers with current bot
```python3
result: Message = await SendVenue(...)
```

#### With specific bot
```python3
result: Message = await bot(SendVenue(...))
```
#### As reply into Webhook in handler
```python3
return SendVenue(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendvenue)
- [aiogram.types.ForceReply](../types/force_reply.md)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.ReplyKeyboardMarkup](../types/reply_keyboard_markup.md)
- [aiogram.types.ReplyKeyboardRemove](../types/reply_keyboard_remove.md)
