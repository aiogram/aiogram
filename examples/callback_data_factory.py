import logging
import random
import uuid
import typing

from aiogram import Bot, Dispatcher, executor, md, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified, Throttled

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'BOT TOKEN HERE'


bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

POSTS = {
    str(uuid.uuid4()): {
        'title': f'Post {index}',
        'body': 'Lorem ipsum dolor sit amet, '
                'consectetur adipiscing elit, '
                'sed do eiusmod tempor incididunt ut '
                'labore et dolore magna aliqua',
        'votes': random.randint(-2, 5),
    } for index in range(1, 6)
}

posts_cb = CallbackData('post', 'id', 'action')  # post:<id>:<action>


def get_keyboard() -> types.InlineKeyboardMarkup:
    """
    Generate keyboard with list of posts
    """
    markup = types.InlineKeyboardMarkup()
    for post_id, post in POSTS.items():
        markup.add(
            types.InlineKeyboardButton(
                post['title'],
                callback_data=posts_cb.new(id=post_id, action='view')),
        )
    return markup


def format_post(post_id: str, post: dict) -> (str, types.InlineKeyboardMarkup):
    text = md.text(
        md.hbold(post['title']),
        md.quote_html(post['body']),
        '',  # just new empty line
        f"Votes: {post['votes']}",
        sep='\n',
    )

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('👍', callback_data=posts_cb.new(id=post_id, action='like')),
        types.InlineKeyboardButton('👎', callback_data=posts_cb.new(id=post_id, action='dislike')),
    )
    markup.add(types.InlineKeyboardButton('<< Back', callback_data=posts_cb.new(id='-', action='list')))
    return text, markup


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.reply('Posts', reply_markup=get_keyboard())


@dp.callback_query_handler(posts_cb.filter(action='list'))
async def query_show_list(query: types.CallbackQuery):
    await query.message.edit_text('Posts', reply_markup=get_keyboard())


@dp.callback_query_handler(posts_cb.filter(action='view'))
async def query_view(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    post_id = callback_data['id']

    post = POSTS.get(post_id, None)
    if not post:
        return await query.answer('Unknown post!')

    text, markup = format_post(post_id, post)
    await query.message.edit_text(text, reply_markup=markup)


@dp.callback_query_handler(posts_cb.filter(action=['like', 'dislike']))
async def query_post_vote(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    try:
        await dp.throttle('vote', rate=1)
    except Throttled:
        return await query.answer('Too many requests.')

    post_id = callback_data['id']
    action = callback_data['action']

    post = POSTS.get(post_id, None)
    if not post:
        return await query.answer('Unknown post!')

    if action == 'like':
        post['votes'] += 1
    elif action == 'dislike':
        post['votes'] -= 1

    await query.answer('Vote accepted')
    text, markup = format_post(post_id, post)
    await query.message.edit_text(text, reply_markup=markup)


@dp.errors_handler(exception=MessageNotModified)
async def message_not_modified_handler(update, error):
    return True # errors_handler must return True if error was handled correctly


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
