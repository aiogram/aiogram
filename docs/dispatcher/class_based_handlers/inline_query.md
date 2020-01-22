# InlineQueryHandler
There is base class for inline query handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import InlineQueryHandler

...

@router.inline_query_handler()
class MyHandler(InlineQueryHandler):
    async def handle(self) -> Any: ...

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.chat` is alias for `self.event.chat`
- `self.query` is alias for `self.event.query`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [InlineQuery](../../api/types/inline_query.md)
- [Router.inline_query_handler](../router.md#inline-query)
