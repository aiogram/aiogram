# PassportElementErrorReverseSide

## Description

Represents an issue with the reverse side of a document. The error is considered resolved when the file with reverse side of the document changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be reverse_side |
| `type` | `#!python str` | The section of the user's Telegram Passport which has the issue, one of 'driver_license', 'identity_card' |
| `file_hash` | `#!python str` | Base64-encoded hash of the file with the reverse side of the document |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorReverseSide`
- `from aiogram.api.types import PassportElementErrorReverseSide`
- `from aiogram.api.types.passport_element_error_reverse_side import PassportElementErrorReverseSide`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrorreverseside)
