# setChatPermissions

## Description

Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the can_restrict_members admin rights. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername) |
| `permissions` | `#!python3 ChatPermissions` | New default chat permissions |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.set_chat_permissions(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetChatPermissions`
- `from aiogram.api.methods import SetChatPermissions`
- `from aiogram.api.methods.set_chat_permissions import SetChatPermissions`

#### In handlers with current bot
```python3
result: bool = await SetChatPermissions(...)
```

#### With specific bot
```python3
result: bool = await bot(SetChatPermissions(...))
```
#### As reply into Webhook in handler
```python3
return SetChatPermissions(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setchatpermissions)
- [aiogram.types.ChatPermissions](../types/chat_permissions.md)
