# CallbackQuery

## Description

This object represents an incoming callback query from a callback button in an inline keyboard. If the button that originated the query was attached to a message sent by the bot, the field message will be present. If the button was attached to a message sent via the bot (in inline mode), the field inline_message_id will be present. Exactly one of the fields data or game_short_name will be present.

NOTE: After the user presses a callback button, Telegram clients will display a progress bar until you call answerCallbackQuery. It is, therefore, necessary to react by calling answerCallbackQuery even if no notification to the user is needed (e.g., without specifying any of the optional parameters).


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Unique identifier for this query |
| `from_user` | `#!python User` | Sender |
| `chat_instance` | `#!python str` | Global identifier, uniquely corresponding to the chat to which the message with the callback button was sent. Useful for high scores in games. |
| `message` | `#!python Optional[Message]` | Optional. Message with the callback button that originated the query. Note that message content and message date will not be available if the message is too old |
| `inline_message_id` | `#!python Optional[str]` | Optional. Identifier of the message sent via the bot in inline mode, that originated the query. |
| `data` | `#!python Optional[str]` | Optional. Data associated with the callback button. Be aware that a bad client can send arbitrary data in this field. |
| `game_short_name` | `#!python Optional[str]` | Optional. Short name of a Game to be returned, serves as the unique identifier for the game |



## Location

- `from aiogram.types import CallbackQuery`
- `from aiogram.api.types import CallbackQuery`
- `from aiogram.api.types.callback_query import CallbackQuery`

## Aliases

Aliases is always returns related API method (Awaitable) and can be used directly or as answer's into webhook.

### Answer

This method has the same specification with the API but without `callback_query_id` argument.

| Answer method         | Alias for                                              | Description                       |
| - | - | - |
| `answer`              | [Bot.answer_callback_query](../methods/answer_callback_query.md)         | Answer to callback query         |

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#callbackquery)
- [aiogram.types.Message](../types/message.md)
- [aiogram.types.User](../types/user.md)
- [aiogram.methods.AnswerCallbackQuery](../methods/answer_callback_query.md)
