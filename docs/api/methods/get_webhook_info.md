# getWebhookInfo

## Description

Use this method to get current webhook status. Requires no parameters. On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.




## Response

Type: `#!python3 WebhookInfo`

Description: On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.


## Usage

### As bot method

```python3
result: WebhookInfo = await bot.get_webhook_info(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetWebhookInfo`
- `from aiogram.api.methods import GetWebhookInfo`
- `from aiogram.api.methods.get_webhook_info import GetWebhookInfo`

#### In handlers with current bot
```python3
result: WebhookInfo = await GetWebhookInfo(...)
```

#### With specific bot
```python3
result: WebhookInfo = await bot(GetWebhookInfo(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getwebhookinfo)
- [aiogram.types.WebhookInfo](../types/webhook_info.md)
