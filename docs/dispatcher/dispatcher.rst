##########
Dispatcher
##########

Dispatcher is root :class:`~aiogram.dispatcher.router.Router` and in code Dispatcher can be used directly for routing updates or attach another routers into dispatcher.

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


.. _Handling updates:

Handling updates
================

All updates can be propagated to the dispatcher by :meth:`~aiogram.dispatcher.dispatcher.Dispatcher.feed_update` method:

.. code-block:: python

  from aiogram import Bot, Dispatcher

  async def update_handler(update: Update, bot: Bot, dispatcher: Dispatcher):
    result = await dp.feed_update(bot, update)

Also you can feed raw update (dictionary) object to the dispatcher by :meth:`~aiogram.dispatcher.dispatcher.Dispatcher.feed_raw_update` method:

.. code-block:: python

  from aiogram import Bot, Dispatcher

  async def update_handler(raw_update: dict[str, Any], bot: Bot, dispatcher: Dispatcher):
    result = await dp.feed_raw_update(bot, raw_update)
