"""
Babel is required.
"""

import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils.executor import start_polling
from aiogram.utils.markdown import *

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.message_handler()
async def check_language(message: types.Message):
    locale = message.from_user.locale

    await message.reply(text(
        bold('Info about your language:'),
        text(' 🔸', bold('Code:'), italic(locale.locale)),
        text(' 🔸', bold('Territory:'), italic(locale.territory or 'Unknown')),
        text(' 🔸', bold('Language name:'), italic(locale.language_name)),
        text(' 🔸', bold('English language name:'), italic(locale.english_name)),
        sep='\n'), parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
