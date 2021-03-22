"""
This is an example with usage of ChatTypeFilter
It filters incoming object based on type of its chat type
"""

import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import ChatType

API_TOKEN = 'BOT TOKEN HERE'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(chat_type=[ChatType.PRIVATE, ChatType.SUPERGROUP])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends message in private chat or supergroup
    """
    await message.reply("Hi!\nI'm hearing your messages in private chats and supergroups")

    # propagate message to the next handler
    raise SkipHandler


@dp.message_handler(chat_type=ChatType.PRIVATE)
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends message in private chat
    """
    await message.reply("Hi!\nI'm hearing your messages only in private chats")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
