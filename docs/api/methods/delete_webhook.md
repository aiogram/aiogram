# deleteWebhook

## Description

Use this method to remove webhook integration if you decide to switch back to getUpdates. Returns True on success. Requires no parameters.




## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.delete_webhook(...)
```

### Method as object

Imports:

- `from aiogram.methods import DeleteWebhook`
- `from aiogram.api.methods import DeleteWebhook`
- `from aiogram.api.methods.delete_webhook import DeleteWebhook`

#### As reply into Webhook
```python3
result: bool = await DeleteWebhook(...)
```

#### With specific bot
```python3
result: bool = await bot(DeleteWebhook(...))
```
#### As reply into Webhook in handler
```python3
return DeleteWebhook(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#deletewebhook)
