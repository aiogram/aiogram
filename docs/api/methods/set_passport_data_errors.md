# setPassportDataErrors

## Description

Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns True on success.

Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.


## Arguments

| Name | Type | Description |
| - | - | - |
| `user_id` | `#!python3 int` | User identifier |
| `errors` | `#!python3 List[PassportElementError]` | A JSON-serialized array describing the errors |



## Response

Type: `#!python3 bool`

Description: The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_passport_data_errors(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetPassportDataErrors`
- `from aiogram.api.methods import SetPassportDataErrors`
- `from aiogram.api.methods.set_passport_data_errors import SetPassportDataErrors`

#### As reply into Webhook
```python3
return SetPassportDataErrors(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(SetPassportDataErrors(...))
```

#### In handlers with current bot
```python3
result: bool = await SetPassportDataErrors(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setpassportdataerrors)
- [aiogram.types.PassportElementError](../types/passport_element_error.md)
