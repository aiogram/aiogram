import asyncio
import logging

from aiogram import Bot, types, Dispatcher, executor

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.inline_handler()
async def inline_echo(inline_query: types.InlineQuery):
    input_content = types.InputTextMessageContent(inline_query.query or 'echo')
    item = types.InlineQueryResultArticle(id='1', title='echo',
                                          input_message_content=input_content)
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)
