# PassportElementErrorTranslationFile

## Description

Represents an issue with one of the files that constitute the translation of a document. The error is considered resolved when the file changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be translation_file |
| `type` | `#!python str` | Type of element of the user's Telegram Passport which has the issue, one of 'passport', 'driver_license', 'identity_card', 'internal_passport', 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration' |
| `file_hash` | `#!python str` | Base64-encoded file hash |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorTranslationFile`
- `from aiogram.api.types import PassportElementErrorTranslationFile`
- `from aiogram.api.types.passport_element_error_translation_file import PassportElementErrorTranslationFile`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrortranslationfile)
