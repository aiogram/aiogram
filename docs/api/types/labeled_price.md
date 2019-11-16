# LabeledPrice

## Description

This object represents a portion of the price for goods or services.


## Attributes

| Name | Type | Description |
| - | - | - |
| `label` | `#!python str` | Portion label |
| `amount` | `#!python int` | Price of the product in the smallest units of the currency (integer, not float/double). For example, for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). |



## Location

- `from aiogram.types import LabeledPrice`
- `from aiogram.api.types import LabeledPrice`
- `from aiogram.api.types.labeled_price import LabeledPrice`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#labeledprice)
