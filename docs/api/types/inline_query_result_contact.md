# InlineQueryResultContact

## Description

Represents a contact with a phone number. By default, this contact will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the contact.

Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be contact |
| `id` | `#!python str` | Unique identifier for this result, 1-64 Bytes |
| `phone_number` | `#!python str` | Contact's phone number |
| `first_name` | `#!python str` | Contact's first name |
| `last_name` | `#!python Optional[str]` | Optional. Contact's last name |
| `vcard` | `#!python Optional[str]` | Optional. Additional data about the contact in the form of a vCard, 0-2048 bytes |
| `reply_markup` | `#!python Optional[InlineKeyboardMarkup]` | Optional. Inline keyboard attached to the message |
| `input_message_content` | `#!python Optional[InputMessageContent]` | Optional. Content of the message to be sent instead of the contact |
| `thumb_url` | `#!python Optional[str]` | Optional. Url of the thumbnail for the result |
| `thumb_width` | `#!python Optional[int]` | Optional. Thumbnail width |
| `thumb_height` | `#!python Optional[int]` | Optional. Thumbnail height |



## Location

- `from aiogram.types import InlineQueryResultContact`
- `from aiogram.api.types import InlineQueryResultContact`
- `from aiogram.api.types.inline_query_result_contact import InlineQueryResultContact`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inlinequeryresultcontact)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMessageContent](../types/input_message_content.md)
