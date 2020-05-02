# promoteChatMember

## Description

Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Pass False for all boolean parameters to demote a user. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `user_id` | `#!python3 int` | Unique identifier of the target user |
| `can_change_info` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can change chat title, photo and other settings |
| `can_post_messages` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can create channel posts, channels only |
| `can_edit_messages` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can edit messages of other users and can pin messages, channels only |
| `can_delete_messages` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can delete messages of other users |
| `can_invite_users` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can invite new users to the chat |
| `can_restrict_members` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can restrict, ban or unban chat members |
| `can_pin_messages` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can pin messages, supergroups only |
| `can_promote_members` | `#!python3 Optional[bool]` | Optional. Pass True, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by him) |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.promote_chat_member(...)
```

### Method as object

Imports:

- `from aiogram.methods import PromoteChatMember`
- `from aiogram.api.methods import PromoteChatMember`
- `from aiogram.api.methods.promote_chat_member import PromoteChatMember`

#### In handlers with current bot
```python3
result: bool = await PromoteChatMember(...)
```

#### With specific bot
```python3
result: bool = await bot(PromoteChatMember(...))
```
#### As reply into Webhook in handler
```python3
return PromoteChatMember(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#promotechatmember)
