# ChosenInlineResultHandler

There is base class for chosen inline result handlers.

## Simple usage:
```pyhton3
from aiogram.handlers import ChosenInlineResultHandler

...

@router.chosen_inline_result()
class MyHandler(ChosenInlineResultHandler):
    async def handle(self) -> Any: ...

```

## Extension

This base handler is subclass of [BaseHandler](basics.md#basehandler) with some extensions:

- `self.chat` is alias for `self.event.chat`
- `self.from_user` is alias for `self.event.from_user`

## Related pages

- [BaseHandler](basics.md#basehandler)
- [ChosenInlineResult](../../api/types/chosen_inline_result.md)
- [Router.chosen_inline_result](../router.md#chosen-inline-query)
