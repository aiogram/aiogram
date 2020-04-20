# getMyCommands

## Description

Use this method to get the current list of the bot's commands. Requires no parameters. Returns Array of BotCommand on success.




## Response

Type: `#!python3 List[BotCommand]`

Description: Returns Array of BotCommand on success.


## Usage

### As bot method

```python3
result: List[BotCommand] = await bot.get_my_commands(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetMyCommands`
- `from aiogram.api.methods import GetMyCommands`
- `from aiogram.api.methods.get_my_commands import GetMyCommands`

#### In handlers with current bot
```python3
result: List[BotCommand] = await GetMyCommands(...)
```

#### With specific bot
```python3
result: List[BotCommand] = await bot(GetMyCommands(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getmycommands)
- [aiogram.types.BotCommand](../types/bot_command.md)
