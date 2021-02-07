.. _cbh-base-handler:

===========
BaseHandler
===========

Base handler is generic abstract class and should be used in all other class-based handlers.

Import: :code:`from aiogram.hanler import BaseHandler`

By default you will need to override only method :code:`async def handle(self) -> Any: ...`

This class is also have an default initializer and you don't need to change it.
Initializer accepts current event and all contextual data and which
can be accessed from the handler through attributes: :code:`event: TelegramEvent` and :code:`data: Dict[Any, str]`

If instance of the bot is specified in context data or current context it can be accessed through *bot* class attribute.

Example
=======

.. code-block:: python

    class MyHandler(BaseHandler[Message]):
        async def handle(self) -> Any:
             await self.event.answer("Hello!")
