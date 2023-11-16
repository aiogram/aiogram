######
Errors
######


Handling errors
===============

Is recommended way that you should use errors inside handlers using try-except block,
but in common cases you can use global errors handler at router or dispatcher level.

If you specify errors handler for router - it will be used for all handlers inside this router.

If you specify errors handler for dispatcher - it will be used for all handlers inside all routers.

.. code-block:: python

    @router.error(ExceptionTypeFilter(MyCustomException), F.update.message.as_("message"))
    async def handle_my_custom_exception(event: ErrorEvent, message: Message):
        # do something with error
        await message.answer("Oops, something went wrong!")


    @router.error()
    async def error_handler(event: ErrorEvent):
        logger.critical("Critical error caused by %s", event.exception, exc_info=True)
        # do something with error
        ...


.. _error-event:

ErrorEvent
==========

.. automodule:: aiogram.types.error_event
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields

.. _error-types:

Error types
===========

.. automodule:: aiogram.exceptions
    :members:
    :member-order: bysource
