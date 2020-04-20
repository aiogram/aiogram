# getGameHighScores

## Description

Use this method to get data for high score tables. Will return the score of the specified user and several of his neighbors in a game. On success, returns an Array of GameHighScore objects.

This method will currently return scores for the target user, plus two of his closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them. Please note that this behavior is subject to change.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | Target user id |
| `chat_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the sent message |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |



## Response

Type: `#!python3 List[GameHighScore]`

Description: Will return the score of the specified user and several of his neighbors in a game. On success, returns an Array of GameHighScore objects. This method will currently return scores for the target user, plus two of his closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them.


## Usage

### As bot method

```python3
result: List[GameHighScore] = await bot.get_game_high_scores(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetGameHighScores`
- `from aiogram.api.methods import GetGameHighScores`
- `from aiogram.api.methods.get_game_high_scores import GetGameHighScores`

#### In handlers with current bot
```python3
result: List[GameHighScore] = await GetGameHighScores(...)
```

#### With specific bot
```python3
result: List[GameHighScore] = await bot(GetGameHighScores(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getgamehighscores)
- [aiogram.types.GameHighScore](../types/game_high_score.md)
