# Invoice

## Description

This object contains basic information about an invoice.


## Attributes

| Name | Type | Description |
| - | - | - |
| `title` | `#!python str` | Product name |
| `description` | `#!python str` | Product description |
| `start_parameter` | `#!python str` | Unique bot deep-linking parameter that can be used to generate this invoice |
| `currency` | `#!python str` | Three-letter ISO 4217 currency code |
| `total_amount` | `#!python int` | Total price in the smallest units of the currency (integer, not float/double). For example, for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). |



## Location

- `from aiogram.types import Invoice`
- `from aiogram.api.types import Invoice`
- `from aiogram.api.types.invoice import Invoice`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#invoice)
