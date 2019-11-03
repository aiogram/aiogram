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


@dp.message_handler(commands='start')
async def start_cmd_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=3)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    btns_text = ('Yes!', 'No!')
    keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))
    # adds buttons as a new row to the existing keyboard
    # the behaviour doesn't depend on row_width attribute

    more_btns_text = (
        "I don't know",
        "Who am i?",
        "Where am i?",
        "Who is there?",
    )
    keyboard_markup.add(*(types.KeyboardButton(text) for text in more_btns_text))
    # adds buttons. New rows are formed according to row_width parameter

    await message.reply("Hi!\nDo you like aiogram?", reply_markup=keyboard_markup)


@dp.message_handler()
async def all_msg_handler(message: types.Message):
    # pressing of a KeyboardButton is the same as sending the regular message with the same text
    # so, to handle the responses from the keyboard, we need to use a message_handler
    # in real bot, it's better to define message_handler(text="...") for each button
    # but here for the simplicity only one handler is defined

    button_text = message.text
    logger.debug('The answer is %r', button_text)  # print the text we've got

    if button_text == 'Yes!':
        reply_text = "That's great"
    elif button_text == 'No!':
        reply_text = "Oh no! Why?"
    else:
        reply_text = "Keep calm...Everything is fine"

    await message.reply(reply_text, reply_markup=types.ReplyKeyboardRemove())
    # with message, we send types.ReplyKeyboardRemove() to hide the keyboard


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
