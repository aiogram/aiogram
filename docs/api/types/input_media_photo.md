# InputMediaPhoto

## Description

Represents a photo to be sent.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be photo |
| `media` | `#!python Union[str, InputFile]` | File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. |
| `caption` | `#!python Optional[str]` | Optional. Caption of the photo to be sent, 0-1024 characters after entities parsing |
| `parse_mode` | `#!python Optional[str]` | Optional. Mode for parsing entities in the photo caption. See formatting options for more details. |



## Location

- `from aiogram.types import InputMediaPhoto`
- `from aiogram.api.types import InputMediaPhoto`
- `from aiogram.api.types.input_media_photo import InputMediaPhoto`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputmediaphoto)
- [aiogram.types.InputFile](../types/input_file.md)
- [How to upload file?](../sending_files.md)
