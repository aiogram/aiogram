Quick start
===========

Simple template
---------------

.. code-block:: python3

    import asyncio
    from aiogram import Bot


    loop = asyncio.get_event_loop()
    bot = Bot('TOKEN', loop)


    async def main():
        bot_info = await bot.get_me()

        print(bot_info.username)


    if __name__ == '__main__':
        try:
            loop.run_until_complete(main())
        except KeyboardInterrupt:
            loop.stop()


Manual
------

First you need to get event loop from asyncio

.. code-block:: python3

    import asyncio

    loop = asyncio.get_event_loop()

Then create bot instance, if you have bot token.

Token you can get from `@BotFather <https://t.me/BotFather>`_

.. code-block:: python3

    from aiogram import Bot

    bot = Bot('TOKEN', loop)


And then you can use Dispather module:

.. code-block:: python3

    from aiogram.dispather import Dispatcher

    dp = Dispatcher(bot)

Dispatcher cah handler updates from telegram bot API.

It have **dp.start_pooling()** method.



