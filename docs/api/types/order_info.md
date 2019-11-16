# OrderInfo

## Description

This object represents information about an order.


## Attributes

| Name | Type | Description |
| - | - | - |
| `name` | `#!python Optional[str]` | Optional. User name |
| `phone_number` | `#!python Optional[str]` | Optional. User's phone number |
| `email` | `#!python Optional[str]` | Optional. User email |
| `shipping_address` | `#!python Optional[ShippingAddress]` | Optional. User shipping address |



## Location

- `from aiogram.types import OrderInfo`
- `from aiogram.api.types import OrderInfo`
- `from aiogram.api.types.order_info import OrderInfo`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#orderinfo)
- [aiogram.types.ShippingAddress](../types/shipping_address.md)
