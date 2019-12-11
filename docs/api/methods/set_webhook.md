# setWebhook

## Description

Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url, containing a JSON-serialized Update. In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns True on success.

If you'd like to make sure that the Webhook request comes from Telegram, we recommend using a secret path in the URL, e.g. https://www.example.com/<token>. Since nobody else knows your bot‘s token, you can be pretty sure it’s us.

Notes

1. You will not be able to receive updates using getUpdates for as long as an outgoing webhook is set up.

2. To use a self-signed certificate, you need to upload your public key certificate using certificate parameter. Please upload as InputFile, sending a String will not work.

3. Ports currently supported for Webhooks: 443, 80, 88, 8443.

NEW! If you're having any trouble setting up webhooks, please check out this amazing guide to Webhooks.


## Arguments

| Name | Type | Description |
| - | - | - |
| `url` | `#!python3 str` | HTTPS url to send updates to. Use an empty string to remove webhook integration |
| `certificate` | `#!python3 Optional[InputFile]` | Optional. Upload your public key certificate so that the root certificate in use can be checked. See our self-signed guide for details. |
| `max_connections` | `#!python3 Optional[int]` | Optional. Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to 40. Use lower values to limit the load on your bot‘s server, and higher values to increase your bot’s throughput. |
| `allowed_updates` | `#!python3 Optional[List[str]]` | Optional. List the types of updates you want your bot to receive. For example, specify ['message', 'edited_channel_post', 'callback_query'] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used. |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_webhook(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetWebhook`
- `from aiogram.api.methods import SetWebhook`
- `from aiogram.api.methods.set_webhook import SetWebhook`

#### As reply into Webhook
```python3
return SetWebhook(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(SetWebhook(...))
```

#### In handlers with current bot
```python3
result: bool = await SetWebhook(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setwebhook)
- [aiogram.types.InputFile](../types/input_file.md)
