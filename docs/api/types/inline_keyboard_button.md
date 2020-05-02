# InlineKeyboardButton

## Description

This object represents one button of an inline keyboard. You must use exactly one of the optional fields.


## Attributes

| Name | Type | Description |
| - | - | - |
| `text` | `#!python str` | Label text on the button |
| `url` | `#!python Optional[str]` | Optional. HTTP or tg:// url to be opened when button is pressed |
| `login_url` | `#!python Optional[LoginUrl]` | Optional. An HTTP URL used to automatically authorize the user. Can be used as a replacement for the Telegram Login Widget. |
| `callback_data` | `#!python Optional[str]` | Optional. Data to be sent in a callback query to the bot when button is pressed, 1-64 bytes |
| `switch_inline_query` | `#!python Optional[str]` | Optional. If set, pressing the button will prompt the user to select one of their chats, open that chat and insert the bot‘s username and the specified inline query in the input field. Can be empty, in which case just the bot’s username will be inserted. |
| `switch_inline_query_current_chat` | `#!python Optional[str]` | Optional. If set, pressing the button will insert the bot‘s username and the specified inline query in the current chat’s input field. Can be empty, in which case only the bot's username will be inserted. |
| `callback_game` | `#!python Optional[CallbackGame]` | Optional. Description of the game that will be launched when the user presses the button. |
| `pay` | `#!python Optional[bool]` | Optional. Specify True, to send a Pay button. |



## Location

- `from aiogram.types import InlineKeyboardButton`
- `from aiogram.api.types import InlineKeyboardButton`
- `from aiogram.api.types.inline_keyboard_button import InlineKeyboardButton`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinekeyboardbutton)
- [aiogram.types.CallbackGame](../types/callback_game.md)
- [aiogram.types.LoginUrl](../types/login_url.md)
