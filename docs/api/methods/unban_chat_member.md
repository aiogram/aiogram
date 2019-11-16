# unbanChatMember

## Description

Use this method to unban a previously kicked user in a supergroup or channel. The user will not return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target group or username of the target supergroup or channel (in the format @username) |
| `user_id` | `#!python3 int` | Unique identifier of the target user |



## Response

Type: `#!python3 bool`

Description: The user will not return to the group or channel automatically, but will be able to join via link, etc. Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.unban_chat_member(...)
```

### Method as object

Imports:

- `from aiogram.types import UnbanChatMember`
- `from aiogram.api.types import UnbanChatMember`
- `from aiogram.api.types.unban_chat_member import UnbanChatMember`

#### As reply into Webhook
```python3
return UnbanChatMember(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(UnbanChatMember(...))
```

#### In handlers with current bot
```python3
result: bool = await UnbanChatMember(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#unbanchatmember)
