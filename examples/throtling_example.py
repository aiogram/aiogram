"""
Example for throttling manager.

You can use that for flood controlling.
"""

import asyncio
import logging

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import Throttled
from aiogram.utils.executor import start_polling

API_TOKEN = "BOT TOKEN HERE"

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)

# Throttling manager does not work without Leaky Bucket.
# Then need to use storages. For example use simple in-memory storage.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    try:
        # Execute throttling manager with rate-limit equal to 2 seconds for key "start"
        await dp.throttle("start", rate=2)
    except Throttled:
        # If request is throttled, the `Throttled` exception will be raised
        await message.reply("Too many requests!")
    else:
        # Otherwise do something
        await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


if __name__ == "__main__":
    start_polling(dp, loop=loop, skip_updates=True)
