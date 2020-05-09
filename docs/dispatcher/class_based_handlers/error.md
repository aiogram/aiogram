# ErrorHandler

There is base class for error handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import ErrorHandler

...

@router.errors()
class MyHandler(ErrorHandler):
    async def handle(self) -> Any:
        log.exception(
            "Cause unexpected exception %s: %s", 
            self.exception_name, 
            self.exception_message
        )
```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `#!python3 self.exception_name` is alias for `#!python3 self.event.__class__.__name__`
- `#!python3 self.exception_message` is alias for `#!python3 str(self.event)`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [Router.errors](../router.md#errors)
- [Filters](../filters/exception.md)
