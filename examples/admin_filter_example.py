import logging

from aiogram import Bot, Dispatcher, types, executor

API_TOKEN = 'API_TOKEN_HERE'


logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)


# checks specified chat
@dp.message_handler(is_chat_admin=-1001241113577)
async def handle_specified(msg: types.Message):
    await msg.answer("You are an admin of the specified chat!")


# checks multiple chats
@dp.message_handler(is_chat_admin=[-1001241113577, -320463906])
async def handle_multiple(msg: types.Message):
    await msg.answer("You are an admin of multiple chats!")


# checks current chat
@dp.message_handler(is_chat_admin=True)
async def handler3(msg: types.Message):
    await msg.answer("You are an admin of the current chat!")


if __name__ == '__main__':
    executor.start_polling(dp)
