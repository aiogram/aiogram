# ChatPermissions

## Description

Describes actions that a non-administrator user is allowed to take in a chat.


## Attributes

| Name | Type | Description |
| - | - | - |
| `can_send_messages` | `#!python Optional[bool]` | Optional. True, if the user is allowed to send text messages, contacts, locations and venues |
| `can_send_media_messages` | `#!python Optional[bool]` | Optional. True, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes, implies can_send_messages |
| `can_send_polls` | `#!python Optional[bool]` | Optional. True, if the user is allowed to send polls, implies can_send_messages |
| `can_send_other_messages` | `#!python Optional[bool]` | Optional. True, if the user is allowed to send animations, games, stickers and use inline bots, implies can_send_media_messages |
| `can_add_web_page_previews` | `#!python Optional[bool]` | Optional. True, if the user is allowed to add web page previews to their messages, implies can_send_media_messages |
| `can_change_info` | `#!python Optional[bool]` | Optional. True, if the user is allowed to change the chat title, photo and other settings. Ignored in public supergroups |
| `can_invite_users` | `#!python Optional[bool]` | Optional. True, if the user is allowed to invite new users to the chat |
| `can_pin_messages` | `#!python Optional[bool]` | Optional. True, if the user is allowed to pin messages. Ignored in public supergroups |



## Location

- `from aiogram.types import ChatPermissions`
- `from aiogram.api.types import ChatPermissions`
- `from aiogram.api.types.chat_permissions import ChatPermissions`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#chatpermissions)
