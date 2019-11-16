# Chat

## Description

This object represents a chat.


## Attributes

| Name | Type | Description |
| - | - | - |
| `id` | `#!python int` | Unique identifier for this chat. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier. |
| `type` | `#!python str` | Type of chat, can be either 'private', 'group', 'supergroup' or 'channel' |
| `title` | `#!python Optional[str]` | Optional. Title, for supergroups, channels and group chats |
| `username` | `#!python Optional[str]` | Optional. Username, for private chats, supergroups and channels if available |
| `first_name` | `#!python Optional[str]` | Optional. First name of the other party in a private chat |
| `last_name` | `#!python Optional[str]` | Optional. Last name of the other party in a private chat |
| `photo` | `#!python Optional[ChatPhoto]` | Optional. Chat photo. Returned only in getChat. |
| `description` | `#!python Optional[str]` | Optional. Description, for groups, supergroups and channel chats. Returned only in getChat. |
| `invite_link` | `#!python Optional[str]` | Optional. Chat invite link, for groups, supergroups and channel chats. Each administrator in a chat generates their own invite links, so the bot must first generate the link using exportChatInviteLink. Returned only in getChat. |
| `pinned_message` | `#!python Optional[Message]` | Optional. Pinned message, for groups, supergroups and channels. Returned only in getChat. |
| `permissions` | `#!python Optional[ChatPermissions]` | Optional. Default chat member permissions, for groups and supergroups. Returned only in getChat. |
| `sticker_set_name` | `#!python Optional[str]` | Optional. For supergroups, name of group sticker set. Returned only in getChat. |
| `can_set_sticker_set` | `#!python Optional[bool]` | Optional. True, if the bot can change the group sticker set. Returned only in getChat. |



## Location

- `from aiogram.types import Chat`
- `from aiogram.api.types import Chat`
- `from aiogram.api.types.chat import Chat`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#chat)
- [aiogram.types.ChatPermissions](../types/chat_permissions.md)
- [aiogram.types.ChatPhoto](../types/chat_photo.md)
- [aiogram.types.Message](../types/message.md)
