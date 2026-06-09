==================
InlineQueryHandler
==================

There is base class for inline query handlers.

Simple usage
============

.. code-block:: python

    from aiogram.handlers import InlineQueryHandler

    ...

    @router.inline_query()
    class MyHandler(InlineQueryHandler):
        async def handle(self) -> Any: ...


Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.chat` is alias for :code:`self.event.chat`
- :code:`self.query` is alias for :code:`self.event.query`
