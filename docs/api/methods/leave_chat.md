# leaveChat

## Description

Use this method for your bot to leave a group, supergroup or channel. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername) |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.leave_chat(...)
```

### Method as object

Imports:

- `from aiogram.types import LeaveChat`
- `from aiogram.api.types import LeaveChat`
- `from aiogram.api.types.leave_chat import LeaveChat`

#### As reply into Webhook
```python3
return LeaveChat(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(LeaveChat(...))
```

#### In handlers with current bot
```python3
result: bool = await LeaveChat(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#leavechat)
