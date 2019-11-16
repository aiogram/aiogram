# PassportElementErrorFrontSide

## Description

Represents an issue with the front side of a document. The error is considered resolved when the file with the front side of the document changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be front_side |
| `type` | `#!python str` | The section of the user's Telegram Passport which has the issue, one of 'passport', 'driver_license', 'identity_card', 'internal_passport' |
| `file_hash` | `#!python str` | Base64-encoded hash of the file with the front side of the document |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorFrontSide`
- `from aiogram.api.types import PassportElementErrorFrontSide`
- `from aiogram.api.types.passport_element_error_front_side import PassportElementErrorFrontSide`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrorfrontside)
