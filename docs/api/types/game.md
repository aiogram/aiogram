# Game

## Description

This object represents a game. Use BotFather to create and edit games, their short names will act as unique identifiers.


## Attributes

| Name | Type | Description |
| - | - | - |
| `title` | `#!python str` | Title of the game |
| `description` | `#!python str` | Description of the game |
| `photo` | `#!python List[PhotoSize]` | Photo that will be displayed in the game message in chats. |
| `text` | `#!python Optional[str]` | Optional. Brief description of the game or high scores included in the game message. Can be automatically edited to include current high scores for the game when the bot calls setGameScore, or manually edited using editMessageText. 0-4096 characters. |
| `text_entities` | `#!python Optional[List[MessageEntity]]` | Optional. Special entities that appear in text, such as usernames, URLs, bot commands, etc. |
| `animation` | `#!python Optional[Animation]` | Optional. Animation that will be displayed in the game message in chats. Upload via BotFather |



## Location

- `from aiogram.types import Game`
- `from aiogram.api.types import Game`
- `from aiogram.api.types.game import Game`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#game)
- [aiogram.types.Animation](../types/animation.md)
- [aiogram.types.MessageEntity](../types/message_entity.md)
- [aiogram.types.PhotoSize](../types/photo_size.md)
