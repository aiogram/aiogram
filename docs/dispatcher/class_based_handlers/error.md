# ErrorHandler

There is base class for error handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import ErrorHandler

...

@router.errors_handler()
class MyHandler(ErrorHandler):
    async def handle(self) -> Any:
        log.exception(
            "Cause unexpected exception %s: %s", 
            self.event.__class__.__name__, 
            self.event
        )
```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler)

## Related pages

- [BaseHandler](basics.md#basehandler)
- [Router.errors_handler](../router.md#errors)
- [Filters](../filters/exception.md)
