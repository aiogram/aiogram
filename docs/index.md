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


## Task list for 3.0

- [ ] Telegram API features
    - [x] Rewrite Telegram types using **pydantic**
    - [x] Rewrite Telegram methods using **pydantic**
    - [x] Rewrite bot class
    - [ ] ...
- [ ] Dispatcher features
    - [ ] Blueprints/Routers
    - [ ] Refactor FSM
    - [ ] Refactor filters
- [ ] Tests
    - [ ] API
        - [x] Sessions
        - [ ] Types
        - [ ] Methods
        - [ ] Client
    - [ ] Dispatcher
        - [ ] ...
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
