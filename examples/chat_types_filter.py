"""
This is an example with usage of ChatTypeFilter
It filters incoming object based on type of its chat type
"""

import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ChatType

API_TOKEN = 'BOT TOKEN HERE'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(chat_types=[ChatType.PRIVATE, ChatType.CHANNEL])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm hearing your messages in private chats and channels")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
