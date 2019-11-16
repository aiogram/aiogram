# PassportElementErrorUnspecified

## Description

Represents an issue in an unspecified place. The error is considered resolved when new data is added.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be unspecified |
| `type` | `#!python str` | Type of element of the user's Telegram Passport which has the issue |
| `element_hash` | `#!python str` | Base64-encoded element hash |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorUnspecified`
- `from aiogram.api.types import PassportElementErrorUnspecified`
- `from aiogram.api.types.passport_element_error_unspecified import PassportElementErrorUnspecified`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrorunspecified)
