import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType

API_TOKEN = TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(commands=['sticker'])
async def save_sticker(message: types.Message):
    async def handle_bad_message(msg: types.Message):
        """
        Handler for unknown messages
        """
        await msg.reply('That is not a sticker!')

    # Create an reply markup (ForceReply)
    markup = types.ForceReply(selective=True)

    # Send reply to user
    await message.reply('Please send me a sticker.', reply_markup=markup)

    # Wait next message
    # It can only be a sticker
    msg = await dp.next_message(message,
                                content_types=[ContentType.STICKER],
                                otherwise=handle_bad_message,
                                include_cancel=True)

    if not msg:
        # If user send /cancel
        return await message.reply('Canceled.')

    # Download file to memory (io.BytesIO)
    photo = await bot.download_file_by_id(msg.sticker.file_id)

    # And you can use other syntax:
    #   photo = io.BytesIO()
    #   await bot.download_file(msg.sticker.file_id, photo)
    # Or use filename for download file to filesystem:
    #   await bot.download_file(msg.sticker.file_id, 'sticker.webp')

    # Send document to user
    await bot.send_document(message.chat.id, photo, caption=msg.sticker.emoji,
                            reply_to_message_id=message.message_id)


async def main():
    count = await dp.skip_updates()
    print(f"Skipped {count} updates.")
    await dp.start_pooling()


if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.stop()
