# PassportFile

## Description

This object represents a file uploaded to Telegram Passport. Currently all Telegram Passport files are in JPEG format when decrypted and don't exceed 10MB.


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file |
| `file_size` | `#!python int` | File size |
| `file_date` | `#!python int` | Unix time when the file was uploaded |



## Location

- `from aiogram.types import PassportFile`
- `from aiogram.api.types import PassportFile`
- `from aiogram.api.types.passport_file import PassportFile`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportfile)
