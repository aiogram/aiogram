"""
Example for throttling manager.

You can use that for flood controlling.
"""

import logging

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import Throttled
from aiogram.utils.executor import start_polling


API_TOKEN = 'BOT_TOKEN_HERE'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)

# Throttling manager does not work without Leaky Bucket.
# You need to use a storage. For example use simple in-memory storage.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    try:
        # Execute throttling manager with rate-limit equal to 2 seconds for key "start"
        await dp.throttle('start', rate=2)
    except Throttled:
        # If request is throttled, the `Throttled` exception will be raised
        await message.reply('Too many requests!')
    else:
        # Otherwise do something
        await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(commands=['hi'])
@dp.throttled(lambda msg, loop, *args, **kwargs: loop.create_task(bot.send_message(msg.from_user.id, "Throttled")),
              rate=5)
# loop is added to the function to run coroutines from it
async def say_hi(message: types.Message):
    await message.answer("Hi")


# the on_throttled object can be either a regular function or coroutine
async def hello_throttled(*args, **kwargs):
    # args will be the same as in the original handler
    # kwargs will be updated with parameters given to .throttled (rate, key, user_id, chat_id)
    print(f"hello_throttled was called with args={args} and kwargs={kwargs}")
    message = args[0]  # as message was the first argument in the original handler
    await message.answer("Throttled")


@dp.message_handler(commands=['hello'])
@dp.throttled(hello_throttled, rate=4)
async def say_hello(message: types.Message):
    await message.answer("Hello!")


@dp.message_handler(commands=['help'])
@dp.throttled(rate=5)
# nothing will happen if the handler will be throttled
async def help_handler(message: types.Message):
    await message.answer('Help!')

if __name__ == '__main__':
    start_polling(dp, skip_updates=True)
