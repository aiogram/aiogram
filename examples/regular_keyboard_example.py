"""
This bot is created for the demonstration of a usage of regular keyboards.
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
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=3)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    keyboard_markup.row(types.KeyboardButton("Yes!"),
                        types.KeyboardButton("No!"))
    # adds buttons as a new row to the existing keyboard
    # the behaviour doesn't depend on row_width attribute

    keyboard_markup.add(types.KeyboardButton("I don't know"),
                        types.KeyboardButton("Who am i?"),
                        types.KeyboardButton("Where am i?"),
                        types.KeyboardButton("Who is there?"))
    # adds buttons. New rows is formed according to row_width parameter

    await message.reply("Hi!\nDo you love aiogram?", reply_markup=keyboard_markup)


@dp.message_handler()
async def all_msg_handler(message: types.Message):
    # pressing of a KeyboardButton is the same as sending the regular message with the same text
    # so, to handle the responses from the keyboard, we need to use a message_handler
    # in real bot, it's better to define message_handler(text="...") for each button
    # but here for the simplicity only one handler is defined

    text_of_button = message.text
    logger.debug(text_of_button) # print the text we got

    if text_of_button == 'Yes!':
        await message.reply("That's great", reply_markup=types.ReplyKeyboardRemove())
    elif text_of_button == 'No!':
        await message.reply("Oh no! Why?", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.reply("Keep calm...Everything is fine", reply_markup=types.ReplyKeyboardRemove())
    # with message, we send types.ReplyKeyboardRemove() to hide the keyboard


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
