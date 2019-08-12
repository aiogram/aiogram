import asyncio

from aiogram import Bot, Dispatcher, executor, filters, types


API_TOKEN = 'BOT_TOKEN_HERE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(filters.CommandStart())
async def send_welcome(message: types.Message):
    # So... At first I want to send something like this:
    await message.reply("Do you want to see many pussies? Are you ready?")

    # Wait a little...
    await asyncio.sleep(1)

    # Good bots should send chat actions...
    await types.ChatActions.upload_photo()

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
    await message.reply_media_group(media=media)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
