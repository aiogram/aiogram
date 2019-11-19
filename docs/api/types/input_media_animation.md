# InputMediaAnimation

## Description

Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound) to be sent.


## Attributes

| Name | Type | Description |
| - | - | - |
| `type` | `#!python str` | Type of the result, must be animation |
| `media` | `#!python Union[str, InputFile]` | File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. |
| `thumb` | `#!python Optional[Union[InputFile, str]]` | Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. |
| `caption` | `#!python Optional[str]` | Optional. Caption of the animation to be sent, 0-1024 characters |
| `parse_mode` | `#!python Optional[str]` | Optional. Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption. |
| `width` | `#!python Optional[int]` | Optional. Animation width |
| `height` | `#!python Optional[int]` | Optional. Animation height |
| `duration` | `#!python Optional[int]` | Optional. Animation duration |



## Location

- `from aiogram.types import InputMediaAnimation`
- `from aiogram.api.types import InputMediaAnimation`
- `from aiogram.api.types.input_media_animation import InputMediaAnimation`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#inputmediaanimation)
- [aiogram.types.InputFile](../types/input_file.md)
- [How to upload file?](../sending_files.md)
