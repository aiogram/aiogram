##########################
Client session middlewares
##########################

In some cases you may want to add some middlewares to the client session to customize the behavior of the client.

Some useful cases that is:

- Log the outgoing requests
- Customize the request parameters
- Handle rate limiting errors and retry the request
- others ...

So, you can do it using client session middlewares.
A client session middleware is a function (or callable class) that receives the request and the next middleware to call.
The middleware can modify the request and then call the next middleware to continue the request processing.

How to register client session middleware?
==========================================

Register using register method
------------------------------

.. code-block:: python

    bot.session.middleware(RequestLogging(ignore_methods=[GetUpdates]))

Register using decorator
------------------------

.. code-block:: python

    @bot.session.middleware()
    async def my_middleware(
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        # do something with request
        return await make_request(bot, method)


Example
=======

Class based session middleware
------------------------------

.. literalinclude:: ../../../aiogram/client/session/middlewares/request_logging.py
    :lines: 16-
    :language: python
    :linenos:

.. note::

    this middleware is already implemented inside aiogram, so, if you want to use it you can
    just import it :code:`from aiogram.client.session.middlewares.request_logging import RequestLogging`


Function based session middleware
---------------------------------

.. code-block:: python

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        try:
            # do something with request
            return await make_request(bot, method)
        finally:
            # do something after request
