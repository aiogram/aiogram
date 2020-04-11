# answerCallbackQuery

## Description

Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, True is returned.

Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via @Botfather and accept the terms. Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.


## Arguments

| Name | Type | Description |
| - | - | - |
| `callback_query_id` | `#!python3 str` | Unique identifier for the query to be answered |
| `text` | `#!python3 Optional[str]` | Optional. Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters |
| `show_alert` | `#!python3 Optional[bool]` | Optional. If true, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to false. |
| `url` | `#!python3 Optional[str]` | Optional. URL that will be opened by the user's client. If you have created a Game and accepted the conditions via @Botfather, specify the URL that opens your game – note that this will only work if the query comes from a callback_game button. |
| `cache_time` | `#!python3 Optional[int]` | Optional. The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0. |



## Response

Type: `#!python3 bool`

Description: On success, True is returned.


## Usage

### As bot method

```python3
result: bool = await bot.answer_callback_query(...)
```

### Method as object

Imports:

- `from aiogram.methods import AnswerCallbackQuery`
- `from aiogram.api.methods import AnswerCallbackQuery`
- `from aiogram.api.methods.answer_callback_query import AnswerCallbackQuery`

#### In handlers with current bot
```python3
result: bool = await AnswerCallbackQuery(...)
```

#### With specific bot
```python3
result: bool = await bot(AnswerCallbackQuery(...))
```
#### As reply into Webhook in handler
```python3
return AnswerCallbackQuery(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#answercallbackquery)
