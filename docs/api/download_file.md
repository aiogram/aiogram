# How to download file?
## Download file manually
First, you must get the `file_id` of the file you want to download. Information about files sent to the bot is contained in [Message](./types/message.md).

For example, download the document that came to the bot.
```python3
file_id = message.document.file_id
```

Then use the [getFile](./methods/get_file.md) method to get `file_path`.
```python3
file = await bot.get_file(file_id)
file_path = file.file_path
```

After that, use the [download_file](#download_file) method from the bot object.

### download_file(...)

Download file by `file_path` to destination.

If you want to automatically create destination (`#!python3 io.BytesIO`) use default
value of destination and handle result of this method.

|Argument|Type|Description|
|---|---|---|
| file_path | `#!python3 str` | File path on Telegram server |
| destination | `#!python3 Optional[Union[BinaryIO, pathlib.Path, str]]` | Filename, file path or instance of `#!python3 io.IOBase`. For e.g. `#!python3 io.BytesIO` (Default: `#!python3 None`) |
| timeout | `#!python3 int` | Total timeout in seconds (Default: `30`) |
| chunk_size | `#!python3 int` | File chunks size (Default: `64 kb`) |
| seek | `#!python3 bool` | Go to start of file when downloading is finished. Used only for destination with `#!python3 typing.BinaryIO` type (Default: `#!python3 True`) |

There are two options where you can download the file: to **disk** or to **binary I/O object**.

### Download file to disk

To download file to disk, you must specify the file name or path where to download the file. In this case, the function will return nothing. 

```python3
await bot.download_file(file_path, "text.txt")
```

### Download file to binary I/O object

To download file to binary I/O object, you must specify an object with the `#!python3 typing.BinaryIO` type or use the default (`#!python3 None`) value.

In the first case, the function will return your object:
```python3
my_object = MyBinaryIO()
result: MyBinaryIO = await bot.download_file(file_path, my_object)
# print(result is my_object)  # True
```

If you leave the default value, an `#!python3 io.BytesIO` object will be created and returned.

```python3
result: io.BytesIO = await bot.download_file(file_path)
```

## Download file in short way

Getting `file_path` manually every time is boring, so you should use the [download](#download) method.

### download(...)

Download file by `file_id` or `Downloadable` object to destination.

If you want to automatically create destination (`#!python3 io.BytesIO`) use default
value of destination and handle result of this method.

|Argument|Type|Description|
|---|---|---|
| file | `#!python3 Union[str, Downloadable]` | file_id or Downloadable object |
| destination | `#!python3 Optional[Union[BinaryIO, pathlib.Path, str]]` | Filename, file path or instance of `#!python3 io.IOBase`. For e.g. `#!python3 io.BytesIO` (Default: `#!python3 None`) |
| timeout | `#!python3 int` | Total timeout in seconds (Default: `30`) |
| chunk_size | `#!python3 int` | File chunks size (Default: `64 kb`) |
| seek | `#!python3 bool` | Go to start of file when downloading is finished. Used only for destination with `#!python3 typing.BinaryIO` type (Default: `#!python3 True`) |

It differs from [download_file](#download_file) **only** in that it accepts `file_id` or an `Downloadable` object (object that contains the `file_id` attribute) instead of `file_path`.

!!! note
    All `Downloadable` objects are listed in Related pages.

You can download a file to [disk](#download-file-to-disk) or to a [binary I/O](#download-file-to-binary-io-object) object in the same way.

Example:

```python3
document = message.document
await bot.download(document)
```

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getfile)
- [aiogram.types.Animation](types/animation.md)
- [aiogram.types.Audio](types/audio.md)
- [aiogram.types.Document](types/document.md)
- [aiogram.types.File](types/file.md)
- [aiogram.types.PassportFile](types/passport_file.md)
- [aiogram.types.PhotoSize](types/photo_size.md)
- [aiogram.types.Sticker](types/sticker.md)
- [aiogram.types.Video](types/video.md)
- [aiogram.types.VideoNote](types/video_note.md)
- [aiogram.types.Voice](types/voice.md)
- [How to upload file?](upload_file.md)
