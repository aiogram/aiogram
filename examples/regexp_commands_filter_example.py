from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, filters
from aiogram.utils import executor


bot = Bot(token='BOT_TOKEN_HERE', parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['item_([0-9]*)']))
async def send_welcome(message: types.Message, regexp_command):
    await message.reply(f"You have requested an item with id <code>{regexp_command.group(1)}</code>")


@dp.message_handler(commands='start')
async def create_deeplink(message: types.Message):
    bot_user = await bot.me
    bot_username = bot_user.username
    deeplink = f'https://t.me/{bot_username}?start=item_12345'
    text = (
        f'Either send a command /item_1234 or follow this link {deeplink} and then click start\n'
        'It also can be hidden in a inline button\n\n'
        'Or just send <code>/start item_123</code>'
    )
    await message.reply(text, disable_web_page_preview=True)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
