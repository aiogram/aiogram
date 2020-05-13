# PreCheckoutQueryHandler

There is base class for callback query handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import PreCheckoutQueryHandler

...

@router.pre_checkout_query()
class MyHandler(PreCheckoutQueryHandler):
    async def handle(self) -> Any: ...

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.from_user` is alias for `self.event.from_user`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [PreCheckoutQuery](../../api/types/pre_checkout_query.md)
- [Router.pre_checkout_query](../router.md#pre-checkout-query)
