# PassportElementErrorSelfie

## Description

Represents an issue with the selfie with a document. The error is considered resolved when the file with the selfie changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be selfie |
| `type` | `#!python str` | The section of the user's Telegram Passport which has the issue, one of 'passport', 'driver_license', 'identity_card', 'internal_passport' |
| `file_hash` | `#!python str` | Base64-encoded hash of the file with the selfie |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorSelfie`
- `from aiogram.api.types import PassportElementErrorSelfie`
- `from aiogram.api.types.passport_element_error_selfie import PassportElementErrorSelfie`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrorselfie)
