# getMe

## Description

A simple method for testing your bot's auth token. Requires no parameters. Returns basic information about the bot in form of a User object.




## Response

Type: `#!python3 User`

Description: Returns basic information about the bot in form of a User object.


## Usage

### As bot method

```python3
result: User = await bot.get_me(...)
```

### Method as object

Imports:

- `from aiogram.methods import GetMe`
- `from aiogram.api.methods import GetMe`
- `from aiogram.api.methods.get_me import GetMe`

#### In handlers with current bot
```python3
result: User = await GetMe(...)
```

#### With specific bot
```python3
result: User = await bot(GetMe(...))
```



## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getme)
- [aiogram.types.User](../types/user.md)
