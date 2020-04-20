# answerPreCheckoutQuery

## Description

Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query. Use this method to respond to such pre-checkout queries. On success, True is returned. Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.


## Arguments

| Name | Type | Description |
| - | - | - |
| `pre_checkout_query_id` | `#!python3 str` | Unique identifier for the query to be answered |
| `ok` | `#!python3 bool` | Specify True if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use False if there are any problems. |
| `error_message` | `#!python3 Optional[str]` | Optional. Required if ok is False. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user. |



## Response

Type: `#!python3 bool`

Description: On success, True is returned.


## Usage

### As bot method

```python3
result: bool = await bot.answer_pre_checkout_query(...)
```

### Method as object

Imports:

- `from aiogram.methods import AnswerPreCheckoutQuery`
- `from aiogram.api.methods import AnswerPreCheckoutQuery`
- `from aiogram.api.methods.answer_pre_checkout_query import AnswerPreCheckoutQuery`

#### In handlers with current bot
```python3
result: bool = await AnswerPreCheckoutQuery(...)
```

#### With specific bot
```python3
result: bool = await bot(AnswerPreCheckoutQuery(...))
```
#### As reply into Webhook in handler
```python3
return AnswerPreCheckoutQuery(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#answerprecheckoutquery)
