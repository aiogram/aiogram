# ChatMember

## Description

This object contains information about one member of a chat.


## Attributes

| Name | Type | Description |
| - | - | - |
| `user` | `#!python User` | Information about the user |
| `status` | `#!python str` | The member's status in the chat. Can be 'creator', 'administrator', 'member', 'restricted', 'left' or 'kicked' |
| `custom_title` | `#!python Optional[str]` | Optional. Owner and administrators only. Custom title for this user |
| `until_date` | `#!python Optional[Union[int, datetime.datetime, datetime.timedelta]]` | Optional. Restricted and kicked only. Date when restrictions will be lifted for this user; unix time |
| `can_be_edited` | `#!python Optional[bool]` | Optional. Administrators only. True, if the bot is allowed to edit administrator privileges of that user |
| `can_post_messages` | `#!python Optional[bool]` | Optional. Administrators only. True, if the administrator can post in the channel; channels only |
| `can_edit_messages` | `#!python Optional[bool]` | Optional. Administrators only. True, if the administrator can edit messages of other users and can pin messages; channels only |
| `can_delete_messages` | `#!python Optional[bool]` | Optional. Administrators only. True, if the administrator can delete messages of other users |
| `can_restrict_members` | `#!python Optional[bool]` | Optional. Administrators only. True, if the administrator can restrict, ban or unban chat members |
| `can_promote_members` | `#!python Optional[bool]` | Optional. Administrators only. True, if the administrator can add new administrators with a subset of his own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user) |
| `can_change_info` | `#!python Optional[bool]` | Optional. Administrators and restricted only. True, if the user is allowed to change the chat title, photo and other settings |
| `can_invite_users` | `#!python Optional[bool]` | Optional. Administrators and restricted only. True, if the user is allowed to invite new users to the chat |
| `can_pin_messages` | `#!python Optional[bool]` | Optional. Administrators and restricted only. True, if the user is allowed to pin messages; groups and supergroups only |
| `is_member` | `#!python Optional[bool]` | Optional. Restricted only. True, if the user is a member of the chat at the moment of the request |
| `can_send_messages` | `#!python Optional[bool]` | Optional. Restricted only. True, if the user is allowed to send text messages, contacts, locations and venues |
| `can_send_media_messages` | `#!python Optional[bool]` | Optional. Restricted only. True, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes |
| `can_send_polls` | `#!python Optional[bool]` | Optional. Restricted only. True, if the user is allowed to send polls |
| `can_send_other_messages` | `#!python Optional[bool]` | Optional. Restricted only. True, if the user is allowed to send animations, games, stickers and use inline bots |
| `can_add_web_page_previews` | `#!python Optional[bool]` | Optional. Restricted only. True, if the user is allowed to add web page previews to their messages |



## Location

- `from aiogram.types import ChatMember`
- `from aiogram.api.types import ChatMember`
- `from aiogram.api.types.chat_member import ChatMember`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#chatmember)
- [aiogram.types.User](../types/user.md)
