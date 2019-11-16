# sendGame

## Description

Use this method to send a game. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 int` | Unique identifier for the target chat |
| `game_short_name` | `#!python3 str` | Short name of the game, serves as the unique identifier for the game. Set up your games via Botfather. |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for an inline keyboard. If empty, one ‘Play game_title’ button will be shown. If not empty, the first button must launch the game. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_game(...)
```

### Method as object

Imports:

- `from aiogram.types import SendGame`
- `from aiogram.api.types import SendGame`
- `from aiogram.api.types.send_game import SendGame`

#### As reply into Webhook
```python3
return SendGame(...)
```

#### With specific bot
```python3
result: Message = await bot.emit(SendGame(...))
```

#### In handlers with current bot
```python3
result: Message = await SendGame(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendgame)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.Message](../types/message.md)
