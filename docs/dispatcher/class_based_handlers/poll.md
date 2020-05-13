# PollHandler

There is base class for poll handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import PollHandler

...

@router.poll()
class MyHandler(PollHandler):
    async def handle(self) -> Any: ...

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.question` is alias for `self.event.question`
- `self.options` is alias for `self.event.options`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [Poll](../../api/types/poll.md)
- [Router.poll](../router.md#poll)
