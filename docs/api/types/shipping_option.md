# ShippingOption

## Description

This object represents one shipping option.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Shipping option identifier |
| `title` | `#!python str` | Option title |
| `prices` | `#!python List[LabeledPrice]` | List of price portions |



## Location

- `from aiogram.types import ShippingOption`
- `from aiogram.api.types import ShippingOption`
- `from aiogram.api.types.shipping_option import ShippingOption`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#shippingoption)
- [aiogram.types.LabeledPrice](../types/labeled_price.md)
