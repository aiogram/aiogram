# sendInvoice

## Description

Use this method to send invoices. On success, the sent Message is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 int` | Unique identifier for the target private chat |
| `title` | `#!python3 str` | Product name, 1-32 characters |
| `description` | `#!python3 str` | Product description, 1-255 characters |
| `payload` | `#!python3 str` | Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes. |
| `provider_token` | `#!python3 str` | Payments provider token, obtained via Botfather |
| `start_parameter` | `#!python3 str` | Unique deep-linking parameter that can be used to generate this invoice when used as a start parameter |
| `currency` | `#!python3 str` | Three-letter ISO 4217 currency code, see more on currencies |
| `prices` | `#!python3 List[LabeledPrice]` | Price breakdown, a list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.) |
| `provider_data` | `#!python3 Optional[str]` | Optional. JSON-encoded data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider. |
| `photo_url` | `#!python3 Optional[str]` | Optional. URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for. |
| `photo_size` | `#!python3 Optional[int]` | Optional. Photo size |
| `photo_width` | `#!python3 Optional[int]` | Optional. Photo width |
| `photo_height` | `#!python3 Optional[int]` | Optional. Photo height |
| `need_name` | `#!python3 Optional[bool]` | Optional. Pass True, if you require the user's full name to complete the order |
| `need_phone_number` | `#!python3 Optional[bool]` | Optional. Pass True, if you require the user's phone number to complete the order |
| `need_email` | `#!python3 Optional[bool]` | Optional. Pass True, if you require the user's email address to complete the order |
| `need_shipping_address` | `#!python3 Optional[bool]` | Optional. Pass True, if you require the user's shipping address to complete the order |
| `send_phone_number_to_provider` | `#!python3 Optional[bool]` | Optional. Pass True, if user's phone number should be sent to provider |
| `send_email_to_provider` | `#!python3 Optional[bool]` | Optional. Pass True, if user's email address should be sent to provider |
| `is_flexible` | `#!python3 Optional[bool]` | Optional. Pass True, if the final price depends on the shipping method |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the message silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the message is a reply, ID of the original message |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for an inline keyboard. If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button. |



## Response

Type: `#!python3 Message`

Description: On success, the sent Message is returned.


## Usage


### As bot method bot

```python3
result: Message = await bot.send_invoice(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendInvoice`
- `from aiogram.api.methods import SendInvoice`
- `from aiogram.api.methods.send_invoice import SendInvoice`

#### In handlers with current bot
```python3
result: Message = await SendInvoice(...)
```

#### With specific bot
```python3
result: Message = await bot(SendInvoice(...))
```
#### As reply into Webhook in handler
```python3
return SendInvoice(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendinvoice)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.LabeledPrice](../types/labeled_price.md)
- [aiogram.types.Message](../types/message.md)
