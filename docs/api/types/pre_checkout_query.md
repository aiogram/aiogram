# PreCheckoutQuery

## Description

This object contains information about an incoming pre-checkout query.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Unique query identifier |
| `from_user` | `#!python User` | User who sent the query |
| `currency` | `#!python str` | Three-letter ISO 4217 currency code |
| `total_amount` | `#!python int` | Total price in the smallest units of the currency (integer, not float/double). For example, for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). |
| `invoice_payload` | `#!python str` | Bot specified invoice payload |
| `shipping_option_id` | `#!python Optional[str]` | Optional. Identifier of the shipping option chosen by the user |
| `order_info` | `#!python Optional[OrderInfo]` | Optional. Order info provided by the user |



## Location

- `from aiogram.types import PreCheckoutQuery`
- `from aiogram.api.types import PreCheckoutQuery`
- `from aiogram.api.types.pre_checkout_query import PreCheckoutQuery`

## Aliases

Aliases is always returns related API method (Awaitable) and can be used directly or as answer's into webhook.

### Answer

This method has the same specification with the API but without `pre_checkout_query_id` argument.

| Answer method         | Alias for                                              | Description                       |
| - | - | - |
| `answer`              | [Bot.answer_pre_checkout_query](../methods/answer_pre_checkout_query.md)         | Answer to pre checkout query         |


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#precheckoutquery)
- [aiogram.types.OrderInfo](../types/order_info.md)
- [aiogram.types.User](../types/user.md)
- [aiogram.methods.AnswerPreCheckoutQuery](../methods/answer_pre_checkout_query.md)
