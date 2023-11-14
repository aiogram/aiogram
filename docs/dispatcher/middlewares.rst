.. _middlewares:

===========
Middlewares
===========

**aiogram** provides powerful mechanism for customizing event handlers via middlewares.

Middlewares in bot framework seems like Middlewares mechanism in web-frameworks
like `aiohttp <https://docs.aiohttp.org/en/stable/web_advanced.html#aiohttp-web-middlewares>`_,
`fastapi <https://fastapi.tiangolo.com/tutorial/middleware/>`_,
`Django <https://docs.djangoproject.com/en/3.0/topics/http/middleware/>`_ or etc.)
with small difference - here is implemented two layers of middlewares (before and after filters).

.. note::

    Middleware is function that triggered on every event received from
    Telegram Bot API in many points on processing pipeline.

Base theory
===========

As many books and other literature in internet says:

   Middleware is reusable software that leverages patterns and frameworks to bridge
   the gap between the functional requirements of applications and the underlying operating systems,
   network protocol stacks, and databases.

Middleware can modify, extend or reject processing event in many places of pipeline.

Basics
======

Middleware instance can be applied for every type of Telegram Event (Update, Message, etc.) in two places

1. Outer scope - before processing filters (:code:`<router>.<event>.outer_middleware(...)`)
2. Inner scope - after processing filters but before handler (:code:`<router>.<event>.middleware(...)`)

.. image:: ../_static/basics_middleware.png
    :alt: Middleware basics

.. attention::

    Middleware should be subclass of :code:`BaseMiddleware` (:code:`from aiogram import BaseMiddleware`) or any async callable

Arguments specification
=======================

.. autoclass:: aiogram.dispatcher.middlewares.base.BaseMiddleware
    :members:
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__, __call__
    :undoc-members: True


Examples
========

.. danger::

    Middleware should always call :code:`await handler(event, data)` to propagate event for next middleware/handler.
    If you want to stop processing event in middleware you should not call :code:`await handler(event, data)`.


Class-based
-----------
.. code-block:: python

    from aiogram import BaseMiddleware
    from aiogram.types import Message


    class CounterMiddleware(BaseMiddleware):
        def __init__(self) -> None:
            self.counter = 0

        async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
        ) -> Any:
            self.counter += 1
            data['counter'] = self.counter
            return await handler(event, data)

and then

.. code-block:: python3

    router = Router()
    router.message.middleware(CounterMiddleware())


Function-based
--------------

.. code-block:: python3

    @dispatcher.update.outer_middleware()
    async def database_transaction_middleware(
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        async with database.transaction():
            return await handler(event, data)


Facts
=====

1. Middlewares from outer scope will be called on every incoming event
2. Middlewares from inner scope will be called only when filters pass
3. Inner middlewares is always calls for :class:`aiogram.types.update.Update` event type in due to all incoming updates going to specific event type handler through built in update handler
