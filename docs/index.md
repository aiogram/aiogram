# Overview

Documentation for version 3.0 [WIP] [^1]

[![MIT License](https://img.shields.io/pypi/l/aiogram.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Supported python versions](https://img.shields.io/pypi/pyversions/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-4.4-blue.svg?style=flat-square&logo=telegram)](https://core.telegram.org/bots/api)
[![PyPi Package Version](https://img.shields.io/pypi/v/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![PyPi status](https://img.shields.io/pypi/status/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![Downloads](https://img.shields.io/pypi/dm/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![\[Telegram\] aiogram live](https://img.shields.io/badge/telegram-aiogram-blue.svg?style=flat-square)](https://t.me/aiogram_live)

**aiogram** modern and fully asynchronous framework for [Telegram Bot API](https://core.telegram.org/bots/api) written in Python 3.7 with [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](https://github.com/aio-libs/aiohttp). It helps you to make your bots faster and simpler.


## Features

- Asynchronous
- [Supports Telegram Bot API v4.4](api/index.md)
- Finite State Machine
- [Replies into Webhook](https://core.telegram.org/bots/faq#how-can-i-make-requests-in-response-to-updates)
- Middlewares
- Updates router (Blueprints)


!!! note
    Before start using **aiogram** is highly recommend to know how to work with [asyncio](https://docs.python.org/3/library/asyncio.html).
    
    Also if you has questions you can go to our community chats in Telegram:
    
    - [English language](https://t.me/aiogram)
    - [Russian language](https://t.me/aiogram_ru)


## Example

Simple usage
```python3 
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.handler import MessageHandler

TOKEN = "42:TOKEN"
dp = Dispatcher()


@dp.message_handler(commands=["start"])
class MyHandler(MessageHandler):
    """
    This handler receive messages with /start command
    """

    async def handle(self):
        await self.bot.send_message(
            chat_id=self.chat.id, text=f"<b>Hello, {self.from_user.full_name}!</b>"
        )


@dp.message_handler(content_types=[types.ContentType.ANY])
async def echo_handler(message: types.Message, bot: Bot):
    """
    Handler will forward received message back to the sender
    """
    await bot.forward_message(
        from_chat_id=message.chat.id, chat_id=message.chat.id, message_id=message.message_id
    )


def main():
    bot = Bot(TOKEN, parse_mode="HTML")
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
```

## Task list for 3.0

- [ ] Telegram API features
    - [x] Rewrite Telegram types using **pydantic**
    - [x] Rewrite Telegram methods using **pydantic**
    - [x] Rewrite bot class
    - [ ] Contextual aliases for methods in types
    - [ ] ...
- [ ] Dispatcher features
    - [x] Blueprints/Routers
    - [ ] Refactor FSM
    - [ ] Refactor filters
    - [ ] Middlewares
- [ ] Tests
    - [x] API
        - [x] Sessions
        - [x] Types
        - [x] Methods
        - [x] Client
    - [ ] Dispatcher
        - [ ] Dispatcher
        - [x] Router
        - [x] Observers
        - [ ] Filters
    - [ ] Utils
        - [x] Helper
        - [ ] ...
- [ ] CI/CD
    - [ ] Publish to PyPi on tag
    - [x] Build docs on push
    - [ ] Code style
        - [ ] Test with coverage on pull-request
        - [x] Test with coverage on push
        - [ ] mypy on pull-request
        - [ ] Flake8 on pull-request


[^1]: work in progress
