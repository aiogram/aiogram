===========
PollHandler
===========

There is base class for poll handlers.

Simple usage
============

.. code-block:: python

    from aiogram.handlers import PollHandler

    ...

    @router.poll()
    class MyHandler(PollHandler):
        async def handle(self) -> Any: ...

Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.question` is alias for :code:`self.event.question`
- :code:`self.options` is alias for :code:`self.event.options`
