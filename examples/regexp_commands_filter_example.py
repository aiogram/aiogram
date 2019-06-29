from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, filters
from aiogram.utils import executor

bot = Bot(token="TOKEN")
dp = Dispatcher(bot)


@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=["item_([0-9]*)"]))
async def send_welcome(message: types.Message, regexp_command):
    await message.reply(
        "You have requested an item with number: {}".format(regexp_command.group(1))
    )


if __name__ == "__main__":
    executor.start_polling(dp)
