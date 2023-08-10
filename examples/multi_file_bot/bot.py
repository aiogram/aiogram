import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from examples.multi_file_bot import handlers

# Bot token can be obtained via https://t.me/BotFather
TOKEN = "42:TOKEN"


async def main() -> None:
    # Dispatcher is a root router
    dp = Dispatcher()
    # Register all the routers from handlers package (make sure they are imported into handlers/__init__.py)
    dp.include_routers(
        handlers.start.start_router,
        handlers.echo.echo_router,

    )

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
