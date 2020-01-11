# sendMediaGroup

## Description

Use this method to send a group of photos or videos as an album. On success, an array of the sent Messages is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `media` | `#!python3 List[Union[InputMediaPhoto, InputMediaVideo]]` | A JSON-serialized array describing photos and videos to be sent, must include 2–10 items |
| `disable_notification` | `#!python3 Optional[bool]` | Optional. Sends the messages silently. Users will receive a notification with no sound. |
| `reply_to_message_id` | `#!python3 Optional[int]` | Optional. If the messages are a reply, ID of the original message |



## Response

Type: `#!python3 List[Message]`

Description: On success, an array of the sent Messages is returned.


## Usage


### As bot method bot

```python3
result: List[Message] = await bot.send_media_group(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendMediaGroup`
- `from aiogram.api.methods import SendMediaGroup`
- `from aiogram.api.methods.send_media_group import SendMediaGroup`

#### In handlers with current bot
```python3
result: List[Message] = await SendMediaGroup(...)
```

#### With specific bot
```python3
result: List[Message] = await bot(SendMediaGroup(...))
```
#### As reply into Webhook in handler
```python3
return SendMediaGroup(...)
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendmediagroup)
- [aiogram.types.InputMediaPhoto](../types/input_media_photo.md)
- [aiogram.types.InputMediaVideo](../types/input_media_video.md)
- [aiogram.types.Message](../types/message.md)
