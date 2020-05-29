# ShippingQuery

## Description

This object contains information about an incoming shipping query.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python str` | Unique query identifier |
| `from_user` | `#!python User` | User who sent the query |
| `invoice_payload` | `#!python str` | Bot specified invoice payload |
| `shipping_address` | `#!python ShippingAddress` | User specified shipping address |



## Location

- `from aiogram.types import ShippingQuery`
- `from aiogram.api.types import ShippingQuery`
- `from aiogram.api.types.shipping_query import ShippingQuery`

## Aliases

Aliases is always returns related API method (Awaitable) and can be used directly or as answer's into webhook.

### Answer

This method has the same specification with the API but without `shipping_query_id` argument.

| Answer method         | Alias for                                              | Description                       |
| - | - | - |
| `answer`              | [Bot.answer_shipping_query](../methods/answer_shipping_query.md)         | Answer to shipping query         |


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#shippingquery)
- [aiogram.types.ShippingAddress](../types/shipping_address.md)
- [aiogram.types.User](../types/user.md)
- [aiogram.methods.AnswerShippingQuery](../methods/answer_shipping_query.md)
