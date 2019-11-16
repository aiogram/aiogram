# User

## Description

This object represents a Telegram user or bot.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python int` | Unique identifier for this user or bot |
| `is_bot` | `#!python bool` | True, if this user is a bot |
| `first_name` | `#!python str` | User‘s or bot’s first name |
| `last_name` | `#!python Optional[str]` | Optional. User‘s or bot’s last name |
| `username` | `#!python Optional[str]` | Optional. User‘s or bot’s username |
| `language_code` | `#!python Optional[str]` | Optional. IETF language tag of the user's language |



## Location

- `from aiogram.types import User`
- `from aiogram.api.types import User`
- `from aiogram.api.types.user import User`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#user)
