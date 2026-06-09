=======================
PreCheckoutQueryHandler
=======================

There is base class for callback query handlers.

Simple usage
============

.. code-block:: python

    from aiogram.handlers import PreCheckoutQueryHandler

    ...

    @router.pre_checkout_query()
    class MyHandler(PreCheckoutQueryHandler):
        async def handle(self) -> Any: ...

Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.from_user` is alias for :code:`self.event.from_user`
