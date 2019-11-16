# InlineKeyboardMarkup

## Description

This object represents an inline keyboard that appears right next to the message it belongs to.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will display unsupported message.


## Attributes

| Name | Type | Description |
| - | - | - |
| `inline_keyboard` | `#!python List[List[InlineKeyboardButton]]` | Array of button rows, each represented by an Array of InlineKeyboardButton objects |



## Location

- `from aiogram.types import InlineKeyboardMarkup`
- `from aiogram.api.types import InlineKeyboardMarkup`
- `from aiogram.api.types.inline_keyboard_markup import InlineKeyboardMarkup`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinekeyboardmarkup)
- [aiogram.types.InlineKeyboardButton](../types/inline_keyboard_button.md)
