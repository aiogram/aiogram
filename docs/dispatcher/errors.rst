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


Updates that can't be validated
-------------------------------

An update received through a webhook (or passed to :code:`Dispatcher.feed_raw_update`
and :code:`Dispatcher.feed_webhook_update` as a dict) that fails validation is skipped:
the webhook answers it with 200 so Telegram does not redeliver it, and the update is lost.
The skip is logged on :code:`aiogram.webhook` with the number of validation errors
(the raw update goes to the same logger at :code:`DEBUG`).

When the raw update has an integer :code:`update_id`, errors handlers also receive an
:code:`ErrorEvent` with the :code:`pydantic.ValidationError` as :code:`event.exception`.
Its :code:`event.update` carries only :code:`update_id`, so every event field
(:code:`event.update.message` and the others) is :code:`None`.
An exception raised by such an errors handler is logged and does not change the answer.

.. code-block:: python

    from pydantic import ValidationError

    @router.error(ExceptionTypeFilter(ValidationError))
    async def skipped_update_handler(event: ErrorEvent):
        logger.warning("Update %d was skipped", event.update.update_id)


Network errors and the bot token
================================

Request URLs of the Bot API contain the bot token. Network errors never contain it:
requests, :meth:`Bot.download_file() <aiogram.client.bot.Bot.download_file>`,
:meth:`Bot.download() <aiogram.client.bot.Bot.download>` and
:class:`~aiogram.types.input_file.URLInputFile` reads raise
:class:`~aiogram.exceptions.TelegramNetworkError` for every transport failure, timeouts included, whose message names the :code:`aiohttp` error type
and the URL with the token shown as :code:`<bot id>:***` (a URL of another host is shown as its
origin only). The error is raised :code:`from None`, so its traceback prints no chained exception.

- :code:`.original` is the :code:`aiohttp` exception. It may contain the token — don't log it.
- :code:`.request_sent` is :code:`False` when the request is known not to have reached the server,
  :code:`True` when a response arrived, and :code:`None` when it is unknown (for example a timeout).
- :code:`.method` is the API method, or :code:`None` for a download.

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
