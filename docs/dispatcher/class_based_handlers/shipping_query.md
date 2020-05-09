# ShippingQueryHandler

There is base class for callback query handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import ShippingQueryHandler

...

@router.shipping_query()
class MyHandler(ShippingQueryHandler):
    async def handle(self) -> Any: ...

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.from_user` is alias for `self.event.from_user`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [ShippingQuery](../../api/types/shipping_query.md)
- [Router.shipping_query](../router.md#shipping-query)
