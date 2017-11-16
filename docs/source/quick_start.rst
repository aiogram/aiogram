Quick start
===========

Simple template
---------------

By first step you need import all modules

.. code-block:: python3

	from aiogram import Bot
	from aiogram.dispatcher import Dispatcher
	from aiogram.utils import executor

In next step you you can initialize bot and dispatcher instances.
Bot token you can get from `@BotFather <https://t.me/BotFather>`_


.. code-block:: python3

	bot = Bot(token='BOT TOKEN HERE')
	dp = Dispatcher(bot)

And next: all bots is needed  command for starting interaction with bot. Register first command handler:

.. code-block:: python3

	@dp.message_handler(commands=['start', 'help'])
	async def send_welcome(message: types.Message):
		await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")

And last step - run long pooling.

.. code-block:: python3

	if __name__ == '__main__':
		executor.start_pooling(dp, on_startup=startup)

Summary
-------

.. code-block:: python3

	from aiogram import Bot
	from aiogram.dispatcher import Dispatcher
	from aiogram.utils import executor

	bot = Bot(token='BOT TOKEN HERE')
	dp = Dispatcher(bot)

	if __name__ == '__main__':
		executor.start_pooling(dp)

