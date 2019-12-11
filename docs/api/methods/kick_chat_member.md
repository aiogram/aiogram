# kickChatMember

## Description

Use this method to kick a user from a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the group on their own using invite links, etc., unless unbanned first. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target group or username of the target supergroup or channel (in the format @channelusername) |
| `user_id` | `#!python3 int` | Unique identifier of the target user |
| `until_date` | `#!python3 Optional[Union[int, datetime.datetime, datetime.timedelta]]` | Optional. Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever |



## Response

Type: `#!python3 bool`

Description: In the case of supergroups and channels, the user will not be able to return to the group on their own using invite links, etc. Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.kick_chat_member(...)
```

### Method as object

Imports:

- `from aiogram.methods import KickChatMember`
- `from aiogram.api.methods import KickChatMember`
- `from aiogram.api.methods.kick_chat_member import KickChatMember`

#### As reply into Webhook
```python3
return KickChatMember(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(KickChatMember(...))
```

#### In handlers with current bot
```python3
result: bool = await KickChatMember(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#kickchatmember)
