Quick start
===========

Simple template
---------------

At first you have to import all necessary modules

.. code-block:: python3

    from aiogram import Bot, Dispatcher, executor, types

Then you have to initialize bot and dispatcher instances.
Bot token you can get from `@BotFather <https://t.me/BotFather>`_


.. code-block:: python3

    bot = Bot(token='BOT TOKEN HERE')
    dp = Dispatcher(bot)

Next step: interaction with bots starts with one command. Register your first command handler:

.. code-block:: python3

    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: types.Message):
        await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")

If you want to handle all messages in the chat simply add handler without filters:

.. code-block:: python

    @dp.message_handler()
    async def echo(message: types.Message):
        await bot.send_message(message.chat.id, message.text)

Last step: run long polling.

.. code-block:: python3

    if __name__ == '__main__':
        executor.start_polling(dp)

Summary
-------

.. code-block:: python3

    from aiogram import Bot, Dispatcher, executor, types

    bot = Bot(token='BOT TOKEN HERE')
    dp = Dispatcher(bot)


    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: types.Message):
        await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


    @dp.message_handler()
    async def echo(message: types.Message):
        await bot.send_message(message.chat.id, message.text)


    if __name__ == '__main__':
        executor.start_polling(dp)
