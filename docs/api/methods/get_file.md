# getFile

## Description

Use this method to get basic info about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a File object is returned. The file can then be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>, where <file_path> is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling getFile again.

Note: This function may not preserve the original file name and MIME type. You should save the file's MIME type and name (if available) when the File object is received.


## Arguments

| Name | Type | Description |
| - | - | - |
| `file_id` | `#!python3 str` | File identifier to get info about |



## Response

Type: `#!python3 File`

Description: On success, a File object is returned.


## Usage


### As bot method bot

```python3
result: File = await bot.get_file(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetFile`
- `from aiogram.api.methods import GetFile`
- `from aiogram.api.methods.get_file import GetFile`


#### With specific bot
```python3
result: File = await bot.emit(GetFile(...))
```

#### In handlers with current bot
```python3
result: File = await GetFile(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getfile)
- [aiogram.types.File](../types/file.md)
