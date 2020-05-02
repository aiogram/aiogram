# InputTextMessageContent

## Description

Represents the content of a text message to be sent as the result of an inline query.


## Attributes

| Name | Type | Description |
| - | - | - |
| `message_text` | `#!python str` | Text of the message to be sent, 1-4096 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Mode for parsing entities in the message text. See formatting options for more details. |
| `disable_web_page_preview` | `#!python Optional[bool]` | Optional. Disables link previews for links in the sent message |



## Location

- `from aiogram.types import InputTextMessageContent`
- `from aiogram.api.types import InputTextMessageContent`
- `from aiogram.api.types.input_text_message_content import InputTextMessageContent`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputtextmessagecontent)
