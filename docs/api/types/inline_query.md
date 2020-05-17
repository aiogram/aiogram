# InlineQuery

## Description

This object represents an incoming inline query. When the user sends an empty query, your bot could return some default or trending results.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Unique identifier for this query |
| `from_user` | `#!python User` | Sender |
| `query` | `#!python str` | Text of the query (up to 256 characters) |
| `offset` | `#!python str` | Offset of the results to be returned, can be controlled by the bot |
| `location` | `#!python Optional[Location]` | Optional. Sender location, only for bots that request user location |



## Location

- `from aiogram.types import InlineQuery`
- `from aiogram.api.types import InlineQuery`
- `from aiogram.api.types.inline_query import InlineQuery`

## Aliases

Aliases is always returns related API method (Awaitable) and can be used directly or as answer's into webhook.

### Answer

This method has the same specification with the API but without `inline_query_id` argument.

| Answer method         | Alias for                                              | Description                       |
| - | - | - |
| `answer`              | [Bot.answer_inline_query](../methods/answer_inline_query.md)         | Answer to inline query         |


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequery)
- [aiogram.types.Location](../types/location.md)
- [aiogram.types.User](../types/user.md)
- [aiogram.methods.AnswerInlineQuery](../methods/answer_inline_query.md)

