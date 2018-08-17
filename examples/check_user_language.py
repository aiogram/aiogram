"""
Babel is required.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, md, types

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot)


@dp.message_handler()
async def check_language(message: types.Message):
    locale = message.from_user.locale

    await message.reply(md.text(
        md.bold('Info about your language:'),
        md.text(' 🔸', md.bold('Code:'), md.italic(locale.locale)),
        md.text(' 🔸', md.bold('Territory:'), md.italic(locale.territory or 'Unknown')),
        md.text(' 🔸', md.bold('Language name:'), md.italic(locale.language_name)),
        md.text(' 🔸', md.bold('English language name:'), md.italic(locale.english_name)),
        sep='\n'))


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)
