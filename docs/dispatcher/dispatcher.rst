##########
Dispatcher
##########

Dispatcher is root :obj:`Router` and in code Dispatcher can be used directly for routing updates or attach another routers into dispatcher.

Here is only listed base information about Dispatcher. All about writing handlers, filters and etc. you can find in next pages:

- :ref:`Router <Router>`
- :ref:`Filtering events`


.. autoclass:: aiogram.dispatcher.dispatcher.Dispatcher
    :members: __init__, feed_update, feed_raw_update, feed_webhook_update, start_polling, run_polling, stop_polling


Simple usage
============

Example:

.. code-block:: python

    dp = Dispatcher()

    @dp.message()
    async def message_handler(message: types.Message) -> None:
        await SendMessage(chat_id=message.from_user.id, text=message.text)


Including routers

Example:


.. code-block:: python

    dp = Dispatcher()
    router1 = Router()
    dp.include_router(router1)

Handling updates
================

All updates can be propagated to the dispatcher by :obj:`Dispatcher.feed_update(bot=..., update=...)` method:

.. code-block:: python

    bot = Bot(...)
    dp = Dispathcher()

    ...

    result = await dp.feed_update(bot=bot, update=incoming_update)
