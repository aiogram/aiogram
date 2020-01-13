# deleteMessage

## Description

Use this method to delete a message, including service messages, with the following limitations:

- A message can only be deleted if it was sent less than 48 hours ago.

- Bots can delete outgoing messages in private chats, groups, and supergroups.

- Bots can delete incoming messages in private chats.

- Bots granted can_post_messages permissions can delete outgoing messages in channels.

- If the bot is an administrator of a group, it can delete any message there.

- If the bot has can_delete_messages permission in a supergroup or a channel, it can delete any message there.

Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 int` | Identifier of the message to delete |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.delete_message(...)
```

### Method as object

Imports:

- `from aiogram.methods import DeleteMessage`
- `from aiogram.api.methods import DeleteMessage`
- `from aiogram.api.methods.delete_message import DeleteMessage`

#### In handlers with current bot
```python3
result: bool = await DeleteMessage(...)
```

#### With specific bot
```python3
result: bool = await bot(DeleteMessage(...))
```
#### As reply into Webhook in handler
```python3
return DeleteMessage(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#deletemessage)
