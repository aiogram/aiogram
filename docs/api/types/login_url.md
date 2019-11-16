# LoginUrl

## Description

This object represents a parameter of the inline keyboard button used to automatically authorize a user. Serves as a great replacement for the Telegram Login Widget when the user is coming from Telegram. All the user needs to do is tap/click a button and confirm that they want to log in:

Telegram apps support these buttons as of version 5.7.

Sample bot: @discussbot


## Attributes

| Name | Type | Description |
| - | - | - |
| `url` | `#!python str` | An HTTP URL to be opened with user authorization data added to the query string when the button is pressed. If the user refuses to provide authorization data, the original URL without information about the user will be opened. The data added is the same as described in Receiving authorization data. |
| `forward_text` | `#!python Optional[str]` | Optional. New text of the button in forwarded messages. |
| `bot_username` | `#!python Optional[str]` | Optional. Username of a bot, which will be used for user authorization. See Setting up a bot for more details. If not specified, the current bot's username will be assumed. The url's domain must be the same as the domain linked with the bot. See Linking your domain to the bot for more details. |
| `request_write_access` | `#!python Optional[bool]` | Optional. Pass True to request the permission for your bot to send messages to the user. |



## Location

- `from aiogram.types import LoginUrl`
- `from aiogram.api.types import LoginUrl`
- `from aiogram.api.types.login_url import LoginUrl`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#loginurl)
