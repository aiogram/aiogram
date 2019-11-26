# Dispatcher
Imports:

- Recommended: `#!python3 from aiogram import Dispatcher`
- Real location: `#!python3 from aiogram.dispatcher.dispatcher import Dispatcher`

In code Dispatcher can be used directly for routing updates or attach another routers into dispatcher.

!!! warning

    Dispatcher is root [Router](router.md) and can not be included into another routers.


Here is only listed base information about Dispatcher. All about writing handlers, filters and etc. you can found in next pages:

- [Router](router.md).
- [Observer](observer.md).

## Simple usage
Example:
```python3
dp = Dispatcher()

@dp.message_handler()
async def message_handler(message: types.Message) -> None:
    await SendMessage(chat_id=message.from_user.id, text=message.text)
```


## Including routers
Example:
```python3
dp = Dispatcher()
router1 = Router()
dp.include_router(router1)
```


## Handling updates
All updates can be propagated to the dispatcher by `feed_update` method:

```
bot = Bot(...)
dp = Dispathcher()

...

async for result in dp.feed_update(bot=bot, update=incoming_update):
    print(result)
```

**Method specification**:

| Argument | Type | Description |
| --- | --- | --- |
| `bot` | `Bot` | Bot instance related with current update object |
| `update` | `Update` | Update object |
| `**kwargs` | `Any` | Context related data. Will be propagated to handlers, filters and middlewares  |

### Polling
...

### Webhook
...
