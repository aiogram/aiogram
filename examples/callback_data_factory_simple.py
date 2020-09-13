"""
This is a simple example of usage of CallbackData factory
For more comprehensive example see callback_data_factory.py
"""

import logging
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'BOT_TOKEN_HERE'


bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData('vote', 'action')  # vote:<action>
likes = {}  # user_id: amount_of_likes


def get_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('👍', callback_data=vote_cb.new(action='up')),
        types.InlineKeyboardButton('👎', callback_data=vote_cb.new(action='down')),
    )


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    amount_of_likes = likes.get(message.from_user.id, 0)  # get value if key exists else set to 0
    await message.reply(f'Vote! You have {amount_of_likes} votes now.', reply_markup=get_keyboard())


@dp.callback_query_handler(vote_cb.filter(action=['up', 'down']))
async def callback_vote_action(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logging.info('Got this callback data: %r', callback_data)  # callback_data contains all info from callback data
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_data_action = callback_data['action']
    likes_count = likes.get(query.from_user.id, 0)

    if callback_data_action == 'up':
        likes_count += 1
    else:
        likes_count -= 1

    likes[query.from_user.id] = likes_count  # update amount of likes in storage

    await bot.edit_message_text(
        f'You voted {callback_data_action}! Now you have {likes_count} vote[s].',
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard(),
    )


@dp.errors_handler(exception=MessageNotModified)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True # errors_handler must return True if error was handled correctly


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
