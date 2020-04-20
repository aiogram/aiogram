# setMyCommands

## Description

Use this method to change the list of the bot's commands. Returns True on success.


## Arguments

| Name | Type | Description |
| - | - | - |
| `commands` | `#!python3 List[BotCommand]` | A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified. |



## Response

Type: `#!python3 bool`

Description: Returns True on success.


## Usage

### As bot method

```python3
result: bool = await bot.set_my_commands(...)
```

### Method as object

Imports:

- `from aiogram.methods import SetMyCommands`
- `from aiogram.api.methods import SetMyCommands`
- `from aiogram.api.methods.set_my_commands import SetMyCommands`

#### In handlers with current bot
```python3
result: bool = await SetMyCommands(...)
```

#### With specific bot
```python3
result: bool = await bot(SetMyCommands(...))
```
#### As reply into Webhook in handler
```python3
return SetMyCommands(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#setmycommands)
- [aiogram.types.BotCommand](../types/bot_command.md)
