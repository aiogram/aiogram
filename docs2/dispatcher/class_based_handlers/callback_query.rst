====================
CallbackQueryHandler
====================

There is base class for callback query handlers.

Simple usage
============
.. code-block:: python

    from aiogram.handlers import CallbackQueryHandler

    ...

    @router.callback_query()
    class MyHandler(CallbackQueryHandler):
        async def handle(self) -> Any: ...


Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.from_user` is alias for :code:`self.event.from_user`
- :code:`self.message` is alias for :code:`self.event.message`
- :code:`self.callback_data` is alias for :code:`self.event.data`
