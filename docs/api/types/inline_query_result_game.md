# InlineQueryResultGame

## Description

Represents a Game.

Note: This will only work in Telegram versions released after October 1, 2016. Older clients will not display any inline results if a game result is among them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be game |
| `id` | `#!python str` | Unique identifier for this result, 1-64 bytes |
| `game_short_name` | `#!python str` | Short name of the game |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |



## Location

- `from aiogram.types import InlineQueryResultGame`
- `from aiogram.api.types import InlineQueryResultGame`
- `from aiogram.api.types.inline_query_result_game import InlineQueryResultGame`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultgame)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
