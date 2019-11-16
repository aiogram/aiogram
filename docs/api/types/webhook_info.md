# WebhookInfo

## Description

Contains information about the current status of a webhook.


## Attributes

| Name | Type | Description |
| - | - | - |
| `url` | `#!python str` | Webhook URL, may be empty if webhook is not set up |
| `has_custom_certificate` | `#!python bool` | True, if a custom certificate was provided for webhook certificate checks |
| `pending_update_count` | `#!python int` | Number of updates awaiting delivery |
| `last_error_date` | `#!python Optional[int]` | Optional. Unix time for the most recent error that happened when trying to deliver an update via webhook |
| `last_error_message` | `#!python Optional[str]` | Optional. Error message in human-readable format for the most recent error that happened when trying to deliver an update via webhook |
| `max_connections` | `#!python Optional[int]` | Optional. Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery |
| `allowed_updates` | `#!python Optional[List[str]]` | Optional. A list of update types the bot is subscribed to. Defaults to all update types |



## Location

- `from aiogram.types import WebhookInfo`
- `from aiogram.api.types import WebhookInfo`
- `from aiogram.api.types.webhook_info import WebhookInfo`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#webhookinfo)
