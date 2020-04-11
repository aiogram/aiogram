# KeyboardButton

## Description

This object represents one button of the reply keyboard. For simple text buttons String can be used instead of this object to specify text of the button. Optional fields request_contact, request_location, and request_poll are mutually exclusive.

Note: request_contact and request_location options will only work in Telegram versions released after 9 April, 2016. Older clients will display unsupported message.

Note: request_poll option will only work in Telegram versions released after 23 January, 2020. Older clients will display unsupported message.


## Attributes

| Name | Type | Description |
| - | - | - |
| `text` | `#!python str` | Text of the button. If none of the optional fields are used, it will be sent as a message when the button is pressed |
| `request_contact` | `#!python Optional[bool]` | Optional. If True, the user's phone number will be sent as a contact when the button is pressed. Available in private chats only |
| `request_location` | `#!python Optional[bool]` | Optional. If True, the user's current location will be sent when the button is pressed. Available in private chats only |
| `request_poll` | `#!python Optional[KeyboardButtonPollType]` | Optional. If specified, the user will be asked to create a poll and send it to the bot when the button is pressed. Available in private chats only |



## Location

- `from aiogram.types import KeyboardButton`
- `from aiogram.api.types import KeyboardButton`
- `from aiogram.api.types.keyboard_button import KeyboardButton`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#keyboardbutton)
- [aiogram.types.KeyboardButtonPollType](../types/keyboard_button_poll_type.md)
