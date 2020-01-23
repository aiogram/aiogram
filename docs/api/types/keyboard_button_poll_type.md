# KeyboardButtonPollType

## Description

This object represents type of a poll, which is allowed to be created and sent when the corresponding button is pressed.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python Optional[str]` | Optional. If quiz is passed, the user will be allowed to create only polls in the quiz mode. If regular is passed, only regular polls will be allowed. Otherwise, the user will be allowed to create a poll of any type. |



## Location

- `from aiogram.types import KeyboardButtonPollType`
- `from aiogram.api.types import KeyboardButtonPollType`
- `from aiogram.api.types.keyboard_button_poll_type import KeyboardButtonPollType`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#keyboardbuttonpolltype)
