# setGameScore

## Description

Use this method to set the score of the specified user in a game. On success, if the message was sent by the bot, returns the edited Message, otherwise returns True. Returns an error, if the new score is not greater than the user's current score in the chat and force is False.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | User identifier |
| `score` | `#!python3 int` | New score, must be non-negative |
| `force` | `#!python3 Optional[bool]` | Optional. Pass True, if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters |
| `disable_edit_message` | `#!python3 Optional[bool]` | Optional. Pass True, if the game message should not be automatically edited to include the current scoreboard |
| `chat_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the sent message |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |



## Response

Type: `#!python3 Union[Message, bool]`

Description: On success, if the message was sent by the bot, returns the edited Message, otherwise returns True. Returns an error, if the new score is not greater than the user's current score in the chat and force is False.


## Usage


### As bot method bot

```python3
result: Union[Message, bool] = await bot.set_game_score(...)
```

### Method as object

Imports:

- `from aiogram.types import SetGameScore`
- `from aiogram.api.types import SetGameScore`
- `from aiogram.api.types.set_game_score import SetGameScore`

#### As reply into Webhook
```python3
return SetGameScore(...)
```

#### With specific bot
```python3
result: Union[Message, bool] = await bot.emit(SetGameScore(...))
```

#### In handlers with current bot
```python3
result: Union[Message, bool] = await SetGameScore(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setgamescore)
- [aiogram.types.Message](../types/message.md)
