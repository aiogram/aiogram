"""
This is a bot to show the usage of the builtin Text filter
Instead of a list, a single element can be passed to any filter, it will be treated as list with an element
"""

import logging

from aiogram import Bot, Dispatcher, executor, types


API_TOKEN = 'BOT_TOKEN_HERE'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# if the text is equal to any string in the list
@dp.message_handler(text=['text1', 'text2'])
async def text_in_handler(message: types.Message):
    await message.answer("The message text equals to one of in the list!")


# if the text contains any string
@dp.message_handler(text_contains='example1')
@dp.message_handler(text_contains='example2')
async def text_contains_any_handler(message: types.Message):
    await message.answer("The message text contains any of strings")


# if the text contains all the strings from the list
@dp.message_handler(text_contains=['str1', 'str2'])
async def text_contains_all_handler(message: types.Message):
    await message.answer("The message text contains all strings from the list")


# if the text starts with any string from the list
@dp.message_handler(text_startswith=['prefix1', 'prefix2'])
async def text_startswith_handler(message: types.Message):
    await message.answer("The message text starts with any of prefixes")


# if the text ends with any string from the list
@dp.message_handler(text_endswith=['postfix1', 'postfix2'])
async def text_endswith_handler(message: types.Message):
    await message.answer("The message text ends with any of postfixes")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
