# EncryptedPassportElement

## Description

Contains information about documents or other Telegram Passport elements shared with the bot by the user.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Element type. One of 'personal_details', 'passport', 'driver_license', 'identity_card', 'internal_passport', 'address', 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration', 'phone_number', 'email'. |
| `hash` | `#!python str` | Base64-encoded element hash for using in PassportElementErrorUnspecified |
| `data` | `#!python Optional[str]` | Optional. Base64-encoded encrypted Telegram Passport element data provided by the user, available for 'personal_details', 'passport', 'driver_license', 'identity_card', 'internal_passport' and 'address' types. Can be decrypted and verified using the accompanying EncryptedCredentials. |
| `phone_number` | `#!python Optional[str]` | Optional. User's verified phone number, available only for 'phone_number' type |
| `email` | `#!python Optional[str]` | Optional. User's verified email address, available only for 'email' type |
| `files` | `#!python Optional[List[PassportFile]]` | Optional. Array of encrypted files with documents provided by the user, available for 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration' and 'temporary_registration' types. Files can be decrypted and verified using the accompanying EncryptedCredentials. |
| `front_side` | `#!python Optional[PassportFile]` | Optional. Encrypted file with the front side of the document, provided by the user. Available for 'passport', 'driver_license', 'identity_card' and 'internal_passport'. The file can be decrypted and verified using the accompanying EncryptedCredentials. |
| `reverse_side` | `#!python Optional[PassportFile]` | Optional. Encrypted file with the reverse side of the document, provided by the user. Available for 'driver_license' and 'identity_card'. The file can be decrypted and verified using the accompanying EncryptedCredentials. |
| `selfie` | `#!python Optional[PassportFile]` | Optional. Encrypted file with the selfie of the user holding a document, provided by the user; available for 'passport', 'driver_license', 'identity_card' and 'internal_passport'. The file can be decrypted and verified using the accompanying EncryptedCredentials. |
| `translation` | `#!python Optional[List[PassportFile]]` | Optional. Array of encrypted files with translated versions of documents provided by the user. Available if requested for 'passport', 'driver_license', 'identity_card', 'internal_passport', 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration' and 'temporary_registration' types. Files can be decrypted and verified using the accompanying EncryptedCredentials. |



## Location

- `from aiogram.types import EncryptedPassportElement`
- `from aiogram.api.types import EncryptedPassportElement`
- `from aiogram.api.types.encrypted_passport_element import EncryptedPassportElement`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#encryptedpassportelement)
- [aiogram.types.PassportFile](../types/passport_file.md)
