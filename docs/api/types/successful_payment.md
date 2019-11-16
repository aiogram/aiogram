# SuccessfulPayment

## Description

This object contains basic information about a successful payment.


## Attributes

| Name | Type | Description |
| - | - | - |
| `currency` | `#!python str` | Three-letter ISO 4217 currency code |
| `total_amount` | `#!python int` | Total price in the smallest units of the currency (integer, not float/double). For example, for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). |
| `invoice_payload` | `#!python str` | Bot specified invoice payload |
| `telegram_payment_charge_id` | `#!python str` | Telegram payment identifier |
| `provider_payment_charge_id` | `#!python str` | Provider payment identifier |
| `shipping_option_id` | `#!python Optional[str]` | Optional. Identifier of the shipping option chosen by the user |
| `order_info` | `#!python Optional[OrderInfo]` | Optional. Order info provided by the user |



## Location

- `from aiogram.types import SuccessfulPayment`
- `from aiogram.api.types import SuccessfulPayment`
- `from aiogram.api.types.successful_payment import SuccessfulPayment`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#successfulpayment)
- [aiogram.types.OrderInfo](../types/order_info.md)
