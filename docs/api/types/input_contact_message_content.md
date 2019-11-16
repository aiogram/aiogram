# InputContactMessageContent

## Description

Represents the content of a contact message to be sent as the result of an inline query.


## Attributes

| Name | Type | Description |
| - | - | - |
| `phone_number` | `#!python str` | Contact's phone number |
| `first_name` | `#!python str` | Contact's first name |
| `last_name` | `#!python Optional[str]` | Optional. Contact's last name |
| `vcard` | `#!python Optional[str]` | Optional. Additional data about the contact in the form of a vCard, 0-2048 bytes |



## Location

- `from aiogram.types import InputContactMessageContent`
- `from aiogram.api.types import InputContactMessageContent`
- `from aiogram.api.types.input_contact_message_content import InputContactMessageContent`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputcontactmessagecontent)
