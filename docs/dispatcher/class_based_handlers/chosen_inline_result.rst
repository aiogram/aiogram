=========================
ChosenInlineResultHandler
=========================

There is base class for chosen inline result handlers.

Simple usage
============

.. code-block:: python

    from aiogram.handlers import ChosenInlineResultHandler

    ...

    @router.chosen_inline_result()
    class MyHandler(ChosenInlineResultHandler):
        async def handle(self) -> Any: ...


Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.chat` is alias for :code:`self.event.chat`
- :code:`self.from_user` is alias for :code:`self.event.from_user`
