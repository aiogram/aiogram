# How to download file?

Before you start, read the documentation for the [getFile](./methods/get_file.md) method.

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

After that, use the `download_file` method from the bot object.

### download_file(...)

Download file by file_path to destination.
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
