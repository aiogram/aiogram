# Overview

A handler is a async callable which takes a event with contextual data and returns a response.
In `aiogram` this can be more than just an async function, these allow you to use classes which can be used as Telegram event handlers to structure your event handlers and reuse code by harnessing inheritance and mixins.

There are some base class based handlers what you need to use in your own handlers:

- [BaseHandler](#basehandler)
- [MessageHandler](message.md)
- [CallbackQueryHandler](callback_query.md)
- [ChosenInlineResultHandler](chosen_inline_result.md)
- [InlineQueryHandler](inline_query.md)
- [PollHandler](poll.md)
- [PreCheckoutQueryHandler](pre_checkout_query.md)
- [ShippingQueryHandler](shipping_query.md)

## BaseHandler

Base handler is generic abstract class and should be used in all other class-based handlers.

Import: `#!python3 from aiogram.hanler import BaseHandler`

By default you will need to override only method `#!python3 async def handle(self) -> Any: ...`

This class is also have an default initializer and you don't need to change it. 
Initializer accepts current event and all contextual data and which can be accessed from the handler through attributes: `event: TelegramEvent` and `data: Dict[Any, str]`

If instance of the bot is specified in context data or current context it can be accessed through `bot` class attribute.


### For example:
```python3
class MyHandler(BaseHandler[Message]):
    async def handle(self) -> Any:
         await self.event.answer("Hello!")
```
