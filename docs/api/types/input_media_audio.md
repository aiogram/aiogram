# InputMediaAudio

## Description

Represents an audio file to be treated as music to be sent.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be audio |
| `media` | `#!python Union[str, InputFile]` | File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. |
| `thumb` | `#!python Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `caption` | `#!python Optional[str]` | Optional. Caption of the audio to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `duration` | `#!python Optional[int]` | Optional. Duration of the audio in seconds |
| `performer` | `#!python Optional[str]` | Optional. Performer of the audio |
| `title` | `#!python Optional[str]` | Optional. Title of the audio |



## Location

- `from aiogram.types import InputMediaAudio`
- `from aiogram.api.types import InputMediaAudio`
- `from aiogram.api.types.input_media_audio import InputMediaAudio`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputmediaaudio)
- [aiogram.types.InputFile](../types/input_file.md)
