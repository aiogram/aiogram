import logging
from os import getenv

from aiohttp.web import run_app
from aiohttp.web_app import Application

from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram import Dispatcher, Router, Bot, types, F
from aiogram.methods import SendMessage


TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN")

# Webhook settings
WEBHOOK_HOST = getenv("WEBHOOK_HOST", "https://your.domain")
WEBHOOK_PATH = getenv("WEBHOOK_PATH", "/path/to/api")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Webserver settings
WEBAPP_HOST = getenv("WEBAPP_HOST", "localhost")  # or ip
WEBAPP_PORT = getenv("WEBAPP_PORT", 3001)


router = Router()


@router.message(F.text)
async def echo(message: types.Message):
    # Regular request, add bot: Bot to handler kwargs
    # await bot.send_message(message.chat.id, message.text)

    # or reply INTO webhook
    return SendMessage(chat_id=message.chat.id, text=message.text)


@router.startup()
async def on_startup(bot: Bot, webhook_url: str):
    await bot.set_webhook(webhook_url)


@router.shutdown()
async def on_shutdown(bot: Bot, dispatcher: Dispatcher):
    logging.warning("Shutting down..")

    # Insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

    # Close DB connection (if used)
    await dispatcher.storage.close()
    # Close bot session
    await bot.session.close()

    logging.warning("Bye!")


def main():
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")

    dispatcher = Dispatcher()
    dispatcher["webhook_url"] = WEBHOOK_URL
    dispatcher.include_router(router)

    app = Application()
    app["bot"] = bot

    # Skip updates
    # bot.delete_webhook()

    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dispatcher, bot=bot)

    run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
