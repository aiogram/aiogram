from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.handler import SkipHandler

API_TOKEN = 'API_TOKE_HERE'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_id_to_test = None  # todo: Set id here
chat_id_to_test = user_id_to_test


@dp.message_handler(user=user_id_to_test)
async def handler1(msg: types.Message):
    await bot.send_message(msg.chat.id,
                           "Hello, checking with user=")
    raise SkipHandler


@dp.message_handler(user_id=user_id_to_test)
async def handler2(msg: types.Message):
    await bot.send_message(msg.chat.id,
                           "Hello, checking with user_id=")
    raise SkipHandler


@dp.message_handler(chat=chat_id_to_test)
async def handler3(msg: types.Message):
    await bot.send_message(msg.chat.id,
                           "Hello, checking with chat=")
    raise SkipHandler


@dp.message_handler(chat_id=chat_id_to_test)
async def handler4(msg: types.Message):
    await bot.send_message(msg.chat.id,
                           "Hello, checking with chat_id=")
    raise SkipHandler


@dp.message_handler(user=user_id_to_test, chat_id=chat_id_to_test)
async def handler5(msg: types.Message):
    await bot.send_message(msg.chat.id,
                           "Hello from user= & chat_id=")


@dp.message_handler(user=[user_id_to_test, 123])  # todo: add second id here
async def handler6(msg: types.Message):
    print("Checked with list!")


if __name__ == '__main__':
    executor.start_polling(dp)
