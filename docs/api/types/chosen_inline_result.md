# ChosenInlineResult

## Description

Represents a result of an inline query that was chosen by the user and sent to their chat partner.

Note: It is necessary to enable inline feedback via @Botfather in order to receive these objects in updates.


## Attributes

| Name | Type | Description |
| - | - | - |
| `result_id` | `#!python str` | The unique identifier for the result that was chosen |
| `from_user` | `#!python User` | The user that chose the result |
| `query` | `#!python str` | The query that was used to obtain the result |
| `location` | `#!python Optional[Location]` | Optional. Sender location, only for bots that require user location |
| `inline_message_id` | `#!python Optional[str]` | Optional. Identifier of the sent inline message. Available only if there is an inline keyboard attached to the message. Will be also received in callback queries and can be used to edit the message. |



## Location

- `from aiogram.types import ChosenInlineResult`
- `from aiogram.api.types import ChosenInlineResult`
- `from aiogram.api.types.chosen_inline_result import ChosenInlineResult`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#choseninlineresult)
- [aiogram.types.Location](../types/location.md)
- [aiogram.types.User](../types/user.md)
