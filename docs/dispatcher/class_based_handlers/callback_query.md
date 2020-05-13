# CallbackQueryHandler

There is base class for callback query handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import CallbackQueryHandler

...

@router.callback_query()
class MyHandler(CallbackQueryHandler):
    async def handle(self) -> Any: ...

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.from_user` is alias for `self.event.from_user`
- `self.message` is alias for `self.event.message`
- `self.callback_data` is alias for `self.event.data`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [CallbackQuery](../../api/types/callback_query.md)
- [Router.callback_query](../router.md#callback-query)
