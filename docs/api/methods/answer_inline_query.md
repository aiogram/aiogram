# answerInlineQuery

## Description

Use this method to send answers to an inline query. On success, True is returned.

No more than 50 results per query are allowed.


## Arguments

| Name | Type | Description |
| - | - | - |
| `inline_query_id` | `#!python3 str` | Unique identifier for the answered query |
| `results` | `#!python3 List[InlineQueryResult]` | A JSON-serialized array of results for the inline query |
| `cache_time` | `#!python3 Optional[int]` | Optional. The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300. |
| `is_personal` | `#!python3 Optional[bool]` | Optional. Pass True, if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query |
| `next_offset` | `#!python3 Optional[str]` | Optional. Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don‘t support pagination. Offset length can’t exceed 64 bytes. |
| `switch_pm_text` | `#!python3 Optional[str]` | Optional. If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter switch_pm_parameter |
| `switch_pm_parameter` | `#!python3 Optional[str]` | Optional. Deep-linking parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only A-Z, a-z, 0-9, _ and - are allowed. |



## Response

Type: `#!python3 bool`

Description: On success, True is returned.


## Usage


### As bot method bot

```python3
result: bool = await bot.answer_inline_query(...)
```

### Method as object

Imports:

- `from aiogram.methods import AnswerInlineQuery`
- `from aiogram.api.methods import AnswerInlineQuery`
- `from aiogram.api.methods.answer_inline_query import AnswerInlineQuery`

#### As reply into Webhook
```python3
return AnswerInlineQuery(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(AnswerInlineQuery(...))
```

#### In handlers with current bot
```python3
result: bool = await AnswerInlineQuery(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#answerinlinequery)
- [aiogram.types.InlineQueryResult](../types/inline_query_result.md)
