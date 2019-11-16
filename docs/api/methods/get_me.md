# getMe

## Description

A simple method for testing your bot's auth token. Requires no parameters. Returns basic information about the bot in form of a User object.




## Response

Type: `#!python3 User`

Description: Returns basic information about the bot in form of a User object.


## Usage


### As bot method bot

```python3
result: User = await bot.get_me(...)
```

### Method as object

Imports:

- `from aiogram.types import GetMe`
- `from aiogram.api.types import GetMe`
- `from aiogram.api.types.get_me import GetMe`


#### With specific bot
```python3
result: User = await bot.emit(GetMe(...))
```

#### In handlers with current bot
```python3
result: User = await GetMe(...)
```


## Related pages:

- [Official documentation](https://core.telegram.org/bots/api#getme)
- [aiogram.types.User](../types/user.md)
