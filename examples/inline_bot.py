import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.inline_handler()
async def inline_echo(inline_query: types.InlineQuery):
    item = types.InlineQueryResultArticle('1', 'echo', types.InputTextMessageContent(inline_query.query))
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


if __name__ == '__main__':
    try:
        loop.run_until_complete(dp.start_pooling())
    except KeyboardInterrupt:
        loop.stop()
