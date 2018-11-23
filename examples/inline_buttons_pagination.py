#!/usr/bin/env python
"""Bot to demonstrate inline buttons pagination functionality

Usage:
    ./inline_buttons_pagination.py [<token>]

Available commands are:
    /google QUERY
    /numbers START FINISH
"""
from math import ceil
from typing import Optional, Collection, AsyncGenerator
import asyncio
import logging
import sys
import uuid

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.executor import start_polling
from aiogram.utils.parts import InlineButtonsPaginator

logging.basicConfig(level=logging.INFO)


failed_to_import_google_search_api_library_message = (
    "Failed to import Google-Search-API library, /google command will not work.\n"
    "You can install needed libraries using following commands:\n"
    "pip install fake_useragent future selenium unidecode\n"
    "pip install git+https://github.com/rominf/Google-Search-API")


try:
    from google.google import search as google_search
except ImportError:
    google = None
    logging.warning(failed_to_import_google_search_api_library_message)

API_TOKEN = sys.argv[1] if len(sys.argv) > 1 else 'BOT TOKEN HERE'

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def google(chat_id: int, query: str, reply_to_message_id: int, page_count: int = 100) -> Message:
    def text(page: int) -> str:
        return f"Search results (page {page + 1}/{page_count}):"

    async def buttons(page: int) -> AsyncGenerator[InlineKeyboardButton, None]:
        search_results = google_search(query=query, first_page=page)
        for search_result in search_results:
            url = search_result.link
            if url is not None:
                # A workaround for https://github.com/abenassi/Google-Search-API/issues/71
                name = search_result.name.replace(url, '')
                yield InlineKeyboardButton(text=name, url=url)

    send_message_kwargs = dict(reply_to_message_id=reply_to_message_id)
    buttons_paginator = InlineButtonsPaginator(bot=bot,
                                               dispatcher=dp,
                                               chat_id=chat_id,
                                               text=text,
                                               buttons=buttons,
                                               send_message_kwargs=send_message_kwargs)
    return await buttons_paginator.send_buttons_message(page_count=page_count)


@dp.message_handler(commands=['google'])
async def process_google_command(message: types.Message):
    if google is None:
        await message.reply(text=failed_to_import_google_search_api_library_message)
    else:
        query = message.get_args()
        await google(chat_id=message.chat.id, query=query, reply_to_message_id=message.message_id)


async def numbers(chat_id: int, buttons_texts: Collection[str], reply_to_message_id: int, limit: int = 10) -> Message:
    def callback_data_func(button_index: Optional[int], button_text: Optional[str]) -> str:
        _ = button_index
        return button_text

    def text(page: int) -> str:
        return f"Buttons (page {page + 1}/{page_count}):"

    async def button_callback_handler(callback_query: CallbackQuery) -> None:
        await callback_query.answer()
        button_text = callback_query.data.replace(button_callback_data_prefix, '')
        await callback_query.message.reply(text=f"You have pressed {button_text}")

    async def buttons(page: int) -> AsyncGenerator[InlineKeyboardButton, None]:
        async for button in buttons_paginator.buttons_helper(page=page,
                                                             limit=limit,
                                                             callback_data_func=callback_data_func,
                                                             callback_data_prefix=button_callback_data_prefix,
                                                             buttons_texts=buttons_texts):
            yield button

    page_count = ceil(len(buttons_texts) / limit)
    button_callback_data_prefix = str(uuid.uuid4())
    send_message_kwargs = dict(reply_to_message_id=reply_to_message_id)
    dp.register_callback_query_handler(
        callback=button_callback_handler,
        func=lambda callback_query: callback_query.data.startswith(button_callback_data_prefix),
        state='*')
    buttons_paginator = InlineButtonsPaginator(bot=bot,
                                               dispatcher=dp,
                                               chat_id=chat_id,
                                               text=text,
                                               buttons=buttons,
                                               send_message_kwargs=send_message_kwargs)
    return await buttons_paginator.send_buttons_message(page_count=page_count)


@dp.message_handler(commands=['numbers'])
async def process_numbers_command(message: types.Message):
    start, finish = (int(x) for x in message.get_args().split())
    await numbers(chat_id=message.chat.id,
                  buttons_texts=[str(i) for i in range(start, finish)],
                  reply_to_message_id=message.message_id)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(text="Hi.\nThis bot demonstrates inline buttons pagination functionality.\n"
                             "Available commands are:\n"
                             "/google QUERY\n"
                             "/numbers START FINISH")


if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
