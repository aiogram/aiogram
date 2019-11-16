# PassportData

## Description

Contains information about Telegram Passport data shared with the bot by the user.


## Attributes

| Name | Type | Description |
| - | - | - |
| `data` | `#!python List[EncryptedPassportElement]` | Array with information about documents and other Telegram Passport elements that was shared with the bot |
| `credentials` | `#!python EncryptedCredentials` | Encrypted credentials required to decrypt the data |



## Location

- `from aiogram.types import PassportData`
- `from aiogram.api.types import PassportData`
- `from aiogram.api.types.passport_data import PassportData`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportdata)
- [aiogram.types.EncryptedPassportElement](../types/encrypted_passport_element.md)
- [aiogram.types.EncryptedCredentials](../types/encrypted_credentials.md)
