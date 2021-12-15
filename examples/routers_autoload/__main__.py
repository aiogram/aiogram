from aiogram import Dispatcher, Bot
from aiogram.utils.routers import find_all_routers

from . import config


if __name__ == "__main__":
    bot = Bot(config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # find all routers in routers_autoload.handlers and subdirectories, sub-subdirectories etc.
    # the routers are by default ordered by their indexes (which can be still null)
    # see info about ordering rules in find_all_routers docstring
    routers = find_all_routers("routers_autoload.handlers")

    for r in routers:
        dp.include_router(r)
    dp.run_polling(bot)
