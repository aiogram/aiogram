# ResponseParameters

## Description

Contains information about why a request was unsuccessful.


## Attributes

| Name | Type | Description |
| - | - | - |
| `migrate_to_chat_id` | `#!python Optional[int]` | Optional. The group has been migrated to a supergroup with the specified identifier. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier. |
| `retry_after` | `#!python Optional[int]` | Optional. In case of exceeding flood control, the number of seconds left to wait before the request can be repeated |



## Location

- `from aiogram.types import ResponseParameters`
- `from aiogram.api.types import ResponseParameters`
- `from aiogram.api.types.response_parameters import ResponseParameters`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#responseparameters)
