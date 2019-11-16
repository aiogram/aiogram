# File

## Description

This object represents a file ready to be downloaded. The file can be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling getFile.

Maximum file size to download is 20 MB


## Attributes

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python str` | Identifier for this file |
| `file_size` | `#!python Optional[int]` | Optional. File size, if known |
| `file_path` | `#!python Optional[str]` | Optional. File path. Use https://api.telegram.org/file/bot<token>/<file_path> to get the file. |



## Location

- `from aiogram.types import File`
- `from aiogram.api.types import File`
- `from aiogram.api.types.file import File`

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#file)
