============
ErrorHandler
============

There is base class for error handlers.

Simple usage
============


.. code-block:: python

    from aiogram.handlers import ErrorHandler

    ...

    @router.errors()
    class MyHandler(ErrorHandler):
        async def handle(self) -> Any:
            log.exception(
                "Cause unexpected exception %s: %s",
                self.exception_name,
                self.exception_message
            )

Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.exception_name` is alias for :code:`self.event.__class__.__name__`
- :code:`self.exception_message` is alias for :code:`str(self.event)`
