# sendChatAction

## Description

Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns True on success.

Example: The ImageBot needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use sendChatAction with action = upload_photo. The user will see a 'sending photo' status for the bot.

We only recommend using this method when a response from the bot will take a noticeable amount of time to arrive.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `action` | `#!python3 str` | Type of action to broadcast. Choose one, depending on what the user is about to receive: typing for text messages, upload_photo for photos, record_video or upload_video for videos, record_audio or upload_audio for audio files, upload_document for general files, find_location for location data, record_video_note or upload_video_note for video notes. |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage


### As bot method bot

```python3
result: bool = await bot.send_chat_action(...)
```

### Method as object

Imports:

- `from aiogram.methods import SendChatAction`
- `from aiogram.api.methods import SendChatAction`
- `from aiogram.api.methods.send_chat_action import SendChatAction`

#### As reply into Webhook
```python3
return SendChatAction(...)
```

#### With specific bot
```python3
result: bool = await bot.emit(SendChatAction(...))
```

#### In handlers with current bot
```python3
result: bool = await SendChatAction(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sendchataction)
