# PassportElementErrorFile

## Description

Represents an issue with a document scan. The error is considered resolved when the file with the document scan changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be file |
| `type` | `#!python str` | The section of the user's Telegram Passport which has the issue, one of 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration' |
| `file_hash` | `#!python str` | Base64-encoded file hash |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorFile`
- `from aiogram.api.types import PassportElementErrorFile`
- `from aiogram.api.types.passport_element_error_file import PassportElementErrorFile`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrorfile)
