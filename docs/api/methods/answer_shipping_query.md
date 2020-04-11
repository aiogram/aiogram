# answerShippingQuery

## Description

If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, the Bot API will send an Update with a shipping_query field to the bot. Use this method to reply to shipping queries. On success, True is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `shipping_query_id` | `#!python3 str` | Unique identifier for the query to be answered |
| `ok` | `#!python3 bool` | Specify True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible) |
| `shipping_options` | `#!python3 Optional[List[ShippingOption]]` | Optional. Required if ok is True. A JSON-serialized array of available shipping options. |
| `error_message` | `#!python3 Optional[str]` | Optional. Required if ok is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user. |



## Response

Type: `#!python3 bool`

Description: On success, True is returned.


## Usage

### As bot method

```python3
result: bool = await bot.answer_shipping_query(...)
```

### Method as object

Imports:

- `from aiogram.methods import AnswerShippingQuery`
- `from aiogram.api.methods import AnswerShippingQuery`
- `from aiogram.api.methods.answer_shipping_query import AnswerShippingQuery`

#### In handlers with current bot
```python3
result: bool = await AnswerShippingQuery(...)
```

#### With specific bot
```python3
result: bool = await bot(AnswerShippingQuery(...))
```
#### As reply into Webhook in handler
```python3
return AnswerShippingQuery(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#answershippingquery)
- [aiogram.types.ShippingOption](../types/shipping_option.md)
