# editMessageMedia

## Description

Use this method to edit animation, audio, document, photo, or video messages. If a message is a part of a message album, then it can be edited only to a photo or a video. Otherwise, message type can be changed arbitrarily. When inline message is edited, new file can't be uploaded. Use previously uploaded file via its file_id or specify a URL. On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.


## Arguments

| Name | Type | Description |
| - | - | - |
| `media` | `#!python3 InputMedia` | A JSON-serialized object for a new media content of the message |
| `chat_id` | `#!python3 Optional[Union[int, str]]` | Optional. Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `message_id` | `#!python3 Optional[int]` | Optional. Required if inline_message_id is not specified. Identifier of the message to edit |
| `inline_message_id` | `#!python3 Optional[str]` | Optional. Required if chat_id and message_id are not specified. Identifier of the inline message |
| `reply_markup` | `#!python3 Optional[InlineKeyboardMarkup]` | Optional. A JSON-serialized object for a new inline keyboard. |



## Response

Type: `#!python3 Union[Message, bool]`

Description: On success, if the edited message was sent by the bot, the edited Message is returned, otherwise True is returned.


## Usage


### As bot method bot

```python3
result: Union[Message, bool] = await bot.edit_message_media(...)
```

### Method as object

Imports:

- `from aiogram.methods import EditMessageMedia`
- `from aiogram.api.methods import EditMessageMedia`
- `from aiogram.api.methods.edit_message_media import EditMessageMedia`

#### As reply into Webhook
```python3
return EditMessageMedia(...)
```

#### With specific bot
```python3
result: Union[Message, bool] = await bot.emit(EditMessageMedia(...))
```

#### In handlers with current bot
```python3
result: Union[Message, bool] = await EditMessageMedia(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#editmessagemedia)
- [aiogram.types.InlineKeyboardMarkup](../types/inline_keyboard_markup.md)
- [aiogram.types.InputMedia](../types/input_media.md)
- [aiogram.types.Message](../types/message.md)
