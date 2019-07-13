"""
This bot is created for the demonstration of a usage of inline keyboards.
"""

import logging

from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = 'BOT_TOKEN_HERE'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_cmd_handler(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    keyboard_markup.row(types.InlineKeyboardButton("Yes!", callback_data='yes'),
                        # in real life for the callback_data the callback data factory should be used
                        # here the raw string is used for the simplicity
                        types.InlineKeyboardButton("No!", callback_data='no'))

    keyboard_markup.add(types.InlineKeyboardButton("aiogram link",
                                                   url='https://github.com/aiogram/aiogram'))
    # url buttons has no callback data

    await message.reply("Hi!\nDo you love aiogram?", reply_markup=keyboard_markup)


@dp.callback_query_handler(lambda cb: cb.data in ['yes', 'no'])  # if cb.data is either 'yes' or 'no'
# @dp.callback_query_handler(text='yes') # if cb.data == 'yes'
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer()  # send answer to close the rounding circle

    answer_data = query.data
    logger.debug(f"answer_data={answer_data}")
    # here we can work with query.data
    if answer_data == 'yes':
        await bot.send_message(query.from_user.id, "That's great!")
    elif answer_data == 'no':
        await bot.send_message(query.from_user.id, "Oh no...Why so?")
    else:
        await bot.send_message(query.from_user.id, "Invalid callback data!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
