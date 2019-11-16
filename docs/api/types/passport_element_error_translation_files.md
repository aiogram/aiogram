# PassportElementErrorTranslationFiles

## Description

Represents an issue with the translated version of a document. The error is considered resolved when a file with the document translation change.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be translation_files |
| `type` | `#!python str` | Type of element of the user's Telegram Passport which has the issue, one of 'passport', 'driver_license', 'identity_card', 'internal_passport', 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration' |
| `file_hashes` | `#!python List[str]` | List of base64-encoded file hashes |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorTranslationFiles`
- `from aiogram.api.types import PassportElementErrorTranslationFiles`
- `from aiogram.api.types.passport_element_error_translation_files import PassportElementErrorTranslationFiles`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrortranslationfiles)
