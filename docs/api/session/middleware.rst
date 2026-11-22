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
A client session middleware is an async function (or callable class) that receives one
:class:`~aiogram.client.session.middlewares.base.RequestContext` per API call:
:code:`ctx.bot`, :code:`ctx.method`, :code:`ctx.timeout` and :code:`ctx.attempt`.
It can change them and then continue the request with :code:`await ctx.next()`.

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
    async def my_middleware(ctx: RequestContext[TelegramType]) -> TelegramType:
        # do something with ctx.method
        return await ctx.next()


Order and anchors
=================

Middlewares run in registration order, the first registered outermost. :code:`before=` and
:code:`after=` place a middleware relative to another one: a middleware class (its first
registered instance, subclasses included) or a registered middleware object.

.. code-block:: python

    bot.session.middleware(RateLimitMiddleware())
    bot.session.middleware.register(RetryMiddleware(), before=RateLimitMiddleware)
    # Retry -> RateLimit -> request

    @bot.session.middleware(after=RetryMiddleware)
    async def per_attempt(ctx: RequestContext[TelegramType]) -> TelegramType:
        print("attempt", ctx.attempt)
        return await ctx.next()

The order is resolved at the next API call and reused until the next :code:`register` /
:code:`unregister`. An anchor that is not registered, or anchors that form a cycle, make that call
raise :code:`ValueError` naming them. Iterating :code:`bot.session.middleware` gives the
middlewares in execution order.


The request context
===================

.. autoclass:: aiogram.client.session.middlewares.base.RequestContext
    :members: bot, method, timeout, attempt, next

A retrying middleware calls :code:`ctx.next()` once per attempt and sets :code:`ctx.attempt`
before each call; inner middlewares read it. Calling :code:`ctx.next()` concurrently on one
context is not supported.


Example
=======

Class based session middleware
------------------------------

.. literalinclude:: ../../../aiogram/client/session/middlewares/request_logging.py
    :pyobject: RequestLogging
    :language: python
    :linenos:

.. note::

    this middleware is already implemented inside aiogram, so, if you want to use it you can
    just import it :code:`from aiogram.client.session.middlewares.request_logging import RequestLogging`


Function based session middleware
---------------------------------

.. code-block:: python

    async def my_middleware(ctx: RequestContext[TelegramType]) -> TelegramType:
        try:
            # do something with request
            return await ctx.next()
        finally:
            # do something after request
            ...


Migrating from aiogram 3.x
==========================

A 3.x middleware takes :code:`(make_request, bot, method)`. It still works for one deprecation
window, with a :code:`DeprecationWarning` at registration:

.. code-block:: python

    # 3.x
    async def my_middleware(make_request, bot, method):
        return await make_request(bot, method)

    # 4.x
    async def my_middleware(ctx):
        return await ctx.next()

Replace a method by assigning :code:`ctx.method` before :code:`await ctx.next()`.
:code:`RequestMiddlewareManager.wrap_middlewares` is removed: call the bot or the session instead.
