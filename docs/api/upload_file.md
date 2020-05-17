# How to upload file?

As says [official Telegram Bot API documentation](https://core.telegram.org/bots/api#sending-files) there are three ways to send files (photos, stickers, audio, media, etc.):

If the file is already stored somewhere on the Telegram servers or file is available by the URL, you don't need to reupload it.
But if you need to upload new file just use subclasses of [InputFile](./types/input_file.md). Here is available three different builtin types of input file:

- `#!python3 FSInputFile` - [uploading from file system](#upload-from-file-system)
- `#!python3 BufferedInputFile` - [uploading from buffer](#upload-from-buffer)
- `#!python3 URLInputFile` - [uploading from URL](#upload-from-url)

!!! warning "Be respectful with Telegram"
    Instances of `InputFile` is reusable. That's mean you can create instance of InputFile and sent this file multiple times but Telegram is not recommend to do that and when you upload file once just save their `file_id` and use it in next times.

## Upload from file system
By first step you will need to import InputFile wrapper:
```python3
from aiogram.types import FSInputFile
```

Then you can use it:
```python3
cat = FSInputFile("cat.png")
agenda = FSInputFile("my-document.pdf", filename="agenda-2019-11-19.pdf")
```

### FSInputFile(...)

|Argument|Type|Description|
|---|---|---|
| path | `#!python3 Union[str, Path]` | File path |
| filename | `#!python3 Optional[str]` | Custom filename to be presented to Telegram |
| chunk_size | `#!python3 int` | File chunks size (Default: `64 kb`) |

## Upload from buffer

Files can be also passed from buffer (For example you generate image using [Pillow](https://pillow.readthedocs.io/en/stable/) and the want's to sent it to the Telegram):

Import wrapper:

```python3
from aiogram.types import BufferedInputFile
```

And then you can use it:
```python3
text_file = BufferedInputFile(b"Hello, world!", filename="file.txt")
```

### BufferedInputFile(...)
|Argument|Type|Description|
|---|---|---|
| `buffer` | `#!python3 bytes` | File path |
| `filename` | `#!python3 str` | Custom filename to be presented to Telegram (Required) |
| `chunk_size` | `#!python3 int` | File chunks size (Default: `64 kb`) |

Also you can read buffer from file:

```python3
file = BufferedInputFile.from_file("file.txt")
```

### BufferedInputFile.from_file(...)
|Argument|Type|Description|
|---|---|---|
| `path` | `#!python3 Union[str, Path]` | File path |
| `filename` | `#!python3 Optional[str]` | Custom filename to be presented to Telegram |
| `chunk_size` | `#!python3 int` | File chunks size (Default: `64 kb`) |

## Upload from url

If you need to upload a file from another server, but the direct link is bound to your server's IP, or you want to bypass native [upload limits](https://core.telegram.org/bots/api#sending-files) by URL, you can use [URLInputFile](#urlinputfile).

Import wrapper:

```python3
from aiogram.types import URLInputFile
```

And then you can use it:
```python3
image = URLInputFile("https://www.python.org/static/community_logos/python-powered-h-140x182.png", filename="logo.png")
```

### URLInputFile(...)
|Argument|Type|Description|
|---|---|---|
| `url` | `#!python3 str` | URL |
| `filename` | `#!python3 Optional[str]` | Custom filename to be presented to Telegram |
| `chunk_size` | `#!python3 int` | File chunks size (Default: `64 kb`) |
| `timeout` | `#!python3 int` | Total timeout in seconds (Default: `30`) |

## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#sending-files)
- [aiogram.types.InputFile](types/input_file.md)
- [How to download file?](download_file.md)
