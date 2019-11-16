# PassportElementErrorFiles

## Description

Represents an issue with a list of scans. The error is considered resolved when the list of files containing the scans changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be files |
| `type` | `#!python str` | The section of the user's Telegram Passport which has the issue, one of 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration' |
| `file_hashes` | `#!python List[str]` | List of base64-encoded file hashes |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorFiles`
- `from aiogram.api.types import PassportElementErrorFiles`
- `from aiogram.api.types.passport_element_error_files import PassportElementErrorFiles`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrorfiles)
