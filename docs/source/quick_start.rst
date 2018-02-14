Quick start
===========

Simple template
---------------

At first you have to import all necessary modules

.. code-block:: python3

	from aiogram import Bot, types
	from aiogram.dispatcher import Dispatcher
	from aiogram.utils import executor

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

Last step: run long polling.

.. code-block:: python3

	if __name__ == '__main__':
		executor.start_polling(dp)

Summary
-------

.. code-block:: python3

	from aiogram import Bot, types
	from aiogram.dispatcher import Dispatcher
	from aiogram.utils import executor

	bot = Bot(token='BOT TOKEN HERE')
	dp = Dispatcher(bot)

	@dp.message_handler(commands=['start', 'help'])
	async def send_welcome(message: types.Message):
		await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")

	if __name__ == '__main__':
		executor.start_polling(dp)
