# EncryptedCredentials

## Description

Contains data required for decrypting and authenticating EncryptedPassportElement. See the Telegram Passport Documentation for a complete description of the data decryption and authentication processes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `data` | `#!python str` | Base64-encoded encrypted JSON-serialized data with unique user's payload, data hashes and secrets required for EncryptedPassportElement decryption and authentication |
| `hash` | `#!python str` | Base64-encoded data hash for data authentication |
| `secret` | `#!python str` | Base64-encoded secret, encrypted with the bot's public RSA key, required for data decryption |



## Location

- `from aiogram.types import EncryptedCredentials`
- `from aiogram.api.types import EncryptedCredentials`
- `from aiogram.api.types.encrypted_credentials import EncryptedCredentials`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#encryptedcredentials)
