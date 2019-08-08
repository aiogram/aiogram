import logging

from aiogram import Bot, Dispatcher, types, executor

API_TOKEN = 'API TOKEN HERE'

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)

chat_id = -1001241113577


# checks specified chat
@dp.message_handler(admin_chat_id=chat_id)
async def handler(msg: types.Message):
    await msg.reply(f"You are an admin of the chat '{chat_id}'", reply=False)


# checks current chat
@dp.message_handler(admin_current_chat=True)
async def handler(msg: types.Message):
    await msg.reply("You are an admin of the current chat!", reply=False)


if __name__ == '__main__':
    executor.start_polling(dp)
