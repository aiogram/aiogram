# AIOGram

[![Financial Contributors on Open Collective](https://opencollective.com/aiogram/all/badge.svg?style=flat-square)](https://opencollective.com/aiogram) 
[![\[Telegram\] aiogram live](https://img.shields.io/badge/telegram-aiogram-blue.svg?style=flat-square)](https://t.me/aiogram_live)
[![PyPi Package Version](https://img.shields.io/pypi/v/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![PyPi status](https://img.shields.io/pypi/status/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![Downloads](https://img.shields.io/pypi/dm/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![Supported python versions](https://img.shields.io/pypi/pyversions/aiogram.svg?style=flat-square)](https://pypi.python.org/pypi/aiogram)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-5.2-blue.svg?style=flat-square&logo=telegram)](https://core.telegram.org/bots/api)
[![Documentation Status](https://img.shields.io/readthedocs/aiogram?style=flat-square)](http://docs.aiogram.dev/en/latest/?badge=latest)
[![Github issues](https://img.shields.io/github/issues/aiogram/aiogram.svg?style=flat-square)](https://github.com/aiogram/aiogram/issues)
[![MIT License](https://img.shields.io/pypi/l/aiogram.svg?style=flat-square)](https://opensource.org/licenses/MIT)

**aiogram** is a pretty simple and fully asynchronous framework for [Telegram Bot API](https://core.telegram.org/bots/api) written in Python 3.7 with [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](https://github.com/aio-libs/aiohttp). It helps you to make your bots faster and simpler.


## Examples
<details>
  <summary>📚 Click to see some basic examples</summary>


**Few steps before getting started...**
- First, you should obtain token for your bot from [BotFather](https://t.me/BotFather).
- Install latest stable version of aiogram, simply running `pip install aiogram`

### Simple [`getMe`](https://core.telegram.org/bots/api#getme) request

```python
import asyncio
from aiogram import Bot

BOT_TOKEN = ""

async def main():
    bot = Bot(token=BOT_TOKEN)

    try:
        me = await bot.get_me()
        print(f"🤖 Hello, I'm {me.first_name}.\nHave a nice Day!")
    finally:
        await bot.close()

asyncio.run(main())
```

### Poll BotAPI for updates and process updates

```python
import asyncio
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = ""

async def start_handler(event: types.Message):
    await event.answer(
        f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",
        parse_mode=types.ParseMode.HTML,
    )

async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        disp = Dispatcher(bot=bot)
        disp.register_message_handler(start_handler, commands={"start", "restart"})
        await disp.start_polling()
    finally:
        await bot.close()

asyncio.run(main())
```

### Moar!

You can find more examples in [`examples/`](https://github.com/aiogram/aiogram/tree/dev-2.x/examples) directory

</details>


## Official aiogram resources:
 - News: [@aiogram_live](https://t.me/aiogram_live)
 - Community: [@aiogram](https://t.me/aiogram)
 - Russian community: [@aiogram_ru](https://t.me/aiogram_ru)
 - PyPI: [aiogram](https://pypi.python.org/pypi/aiogram)
 - Documentation: [aiogram site](https://docs.aiogram.dev/en/latest/)
 - Source: [Github repo](https://github.com/aiogram/aiogram)
 - Issues/Bug tracker: [Github issues tracker](https://github.com/aiogram/aiogram/issues)
 - Test bot: [@aiogram_bot](https://t.me/aiogram_bot)

## Contributors

### Code Contributors

This project exists thanks to all the people who contribute. [[Code of conduct](CODE_OF_CONDUCT.md)].
<a href="https://github.com/aiogram/aiogram/graphs/contributors"><img src="https://opencollective.com/aiogram/contributors.svg?width=890&button=false" /></a>

### Financial Contributors

Become a financial contributor and help us sustain our community. [[Contribute](https://opencollective.com/aiogram/contribute)]

#### Individuals

<a href="https://opencollective.com/aiogram"><img src="https://opencollective.com/aiogram/individuals.svg?width=890"></a>

#### Organizations

Support this project with your organization. Your logo will show up here with a link to your website. [[Contribute](https://opencollective.com/aiogram/contribute)]

<a href="https://opencollective.com/aiogram/organization/0/website"><img src="https://opencollective.com/aiogram/organization/0/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/1/website"><img src="https://opencollective.com/aiogram/organization/1/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/2/website"><img src="https://opencollective.com/aiogram/organization/2/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/3/website"><img src="https://opencollective.com/aiogram/organization/3/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/4/website"><img src="https://opencollective.com/aiogram/organization/4/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/5/website"><img src="https://opencollective.com/aiogram/organization/5/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/6/website"><img src="https://opencollective.com/aiogram/organization/6/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/7/website"><img src="https://opencollective.com/aiogram/organization/7/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/8/website"><img src="https://opencollective.com/aiogram/organization/8/avatar.png"></a>
<a href="https://opencollective.com/aiogram/organization/9/website"><img src="https://opencollective.com/aiogram/organization/9/avatar.png"></a>
