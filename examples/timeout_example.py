import asyncio
import logging

from aiogram import Bot, types, filters
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_polling

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop, connection_timeout=5)
dp = Dispatcher(bot)

@dp.message_handler(filters.CommandStart())
async def start(message: types.Message):
    await message.reply_photo(types.InputFile('data/cat.jpg'), f'Cat with Bot\'s timeout: {bot.connection_timeout.total}!')
    await bot.send_photo(message.chat.id, types.InputFile('data/cats.jpg'), 'More cats with timeout 1 second!', timeout=1)

if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)