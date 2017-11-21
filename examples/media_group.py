import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ChatActions
from aiogram.utils.executor import start_polling

API_TOKEN = 'BOT TOKEN HERE'

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # So... By first i want to send something like that:
    await message.reply("Do you want to see many pussies? Are you ready?")

    # And wait few seconds...
    await asyncio.sleep(1)

    # Good bots always must be send chat actions. Or not.
    await ChatActions.upload_photo()

    # Create media group
    media = types.MediaGroup()

    # Attach local file
    media.attach_photo(types.InputFile('data/cat.jpg'), 'Cat!')
    # More local files and more cats!
    media.attach_photo(types.InputFile('data/cats.jpg'), 'More cats!')

    # You can also use URL's
    # For example: get random puss:
    media.attach_photo('http://lorempixel.com/400/200/cats/', 'Random cat.')

    # And you can also use file ID:
    # media.attach_photo('<file_id>', 'cat-cat-cat.')

    # Done! Send media group
    await bot.send_media_group(message.chat.id, media=media, reply_to_message_id=message.message_id)


if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
