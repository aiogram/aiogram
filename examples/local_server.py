import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.bot.api import TelegramAPIServer
from aiogram.types import ContentType

API_TOKEN = 'BOT TOKEN HERE'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create private Bot API server endpoints wrapper
local_server = TelegramAPIServer.from_base('http://localhost')

# Initialize bot with using local server
bot = Bot(token=API_TOKEN, server=local_server)
# ... and dispatcher
dp = Dispatcher(bot)


@dp.message_handler(content_types=ContentType.ANY)
async def echo(message: types.Message):
    await message.copy_to(message.chat.id)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
