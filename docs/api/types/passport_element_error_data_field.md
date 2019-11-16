# PassportElementErrorDataField

## Description

Represents an issue in one of the data fields that was provided by the user. The error is considered resolved when the field's value changes.


## Attributes

| Name | Type | Description |
| - | - | - |
| `source` | `#!python str` | Error source, must be data |
| `type` | `#!python str` | The section of the user's Telegram Passport which has the error, one of 'personal_details', 'passport', 'driver_license', 'identity_card', 'internal_passport', 'address' |
| `field_name` | `#!python str` | Name of the data field which has the error |
| `data_hash` | `#!python str` | Base64-encoded data hash |
| `message` | `#!python str` | Error message |



## Location

- `from aiogram.types import PassportElementErrorDataField`
- `from aiogram.api.types import PassportElementErrorDataField`
- `from aiogram.api.types.passport_element_error_data_field import PassportElementErrorDataField`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#passportelementerrordatafield)
