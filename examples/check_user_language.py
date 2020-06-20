"""
Babel is required.
"""

import logging

from aiogram import Bot, Dispatcher, executor, md, types

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot)


@dp.message_handler()
async def check_language(message: types.Message):
    locale = message.from_user.locale

    await message.reply(md.text(
        md.bold('Info about your language:'),
        md.text('🔸', md.bold('Code:'), md.code(locale.language)),
        md.text('🔸', md.bold('Territory:'), md.code(locale.territory or 'Unknown')),
        md.text('🔸', md.bold('Language name:'), md.code(locale.language_name)),
        md.text('🔸', md.bold('English language name:'), md.code(locale.english_name)),
        sep='\n',
    ))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
