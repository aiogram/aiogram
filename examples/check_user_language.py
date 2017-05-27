import asyncio
import logging

from aiogram.bot import AIOGramBot
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ParseMode
from aiogram.utils.markdown import *

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = AIOGramBot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.message_handler()
async def check_language(message):
    language = message.from_user.language

    await message.reply(text(
        bold('Info about your language:'),
        text(' 🔸', bold('Code:'), italic(language.code)),
        text(' 🔸', bold('Type:'), italic(language.type)),
        text(' 🔸', bold('Title:'), italic(language.title)),
        sep='\n'), parse_mode=ParseMode.MARKDOWN)


async def main():
    count = await dp.skip_updates()
    print(f"Skipped {count} updates.")
    await dp.start_pooling()


if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.stop()
