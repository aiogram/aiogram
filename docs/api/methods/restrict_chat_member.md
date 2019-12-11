# restrictChatMember

## Description

Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate admin rights. Pass True for all permissions to lift restrictions from a user. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername) |
| `user_id` | `#!python3 int` | Unique identifier of the target user |
| `permissions` | `#!python3 ChatPermissions` | New user permissions |
| `until_date` | `#!python3 Optional[Union[int, datetime.datetime, datetime.timedelta]]` | Optional. Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.restrict_chat_member(...)
```

### Method as object

Imports:

- `from aiogram.methods import RestrictChatMember`
- `from aiogram.api.methods import RestrictChatMember`
- `from aiogram.api.methods.restrict_chat_member import RestrictChatMember`

#### As reply into Webhook
```python3
return RestrictChatMember(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(RestrictChatMember(...))
```

#### In handlers with current bot
```python3
result: bool = await RestrictChatMember(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#restrictchatmember)
- [aiogram.types.ChatPermissions](../types/chat_permissions.md)
