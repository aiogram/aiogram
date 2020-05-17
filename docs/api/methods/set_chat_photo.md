# setChatPhoto

## Description

Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `chat_id` | `#!python3 Union[int, str]` | Unique identifier for the target chat or username of the target channel (in the format @channelusername) |
| `photo` | `#!python3 InputFile` | New chat photo, uploaded using multipart/form-data |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.set_chat_photo(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetChatPhoto`
- `from aiogram.api.methods import SetChatPhoto`
- `from aiogram.api.methods.set_chat_photo import SetChatPhoto`

#### In handlers with current bot
```python3
result: bool = await SetChatPhoto(...)
```

#### With specific bot
```python3
result: bool = await bot(SetChatPhoto(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setchatphoto)
- [aiogram.types.InputFile](../types/input_file.md)
- [How to upload file?](../upload_file.md)
