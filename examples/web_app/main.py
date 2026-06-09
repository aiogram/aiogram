import logging
import sys
from os import getenv

from aiohttp.web import run_app
from aiohttp.web_app import Application

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from handlers import my_router
from routes import check_data_handler, demo_handler, send_message_handler

TOKEN = getenv("BOT_TOKEN")

APP_BASE_URL = getenv("APP_BASE_URL")


async def on_startup(bot: Bot, base_url: str) -> None:
    await bot.set_webhook(f"{base_url}/webhook")
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Open Menu", web_app=WebAppInfo(url=f"{base_url}/demo")),
    )


def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher["base_url"] = APP_BASE_URL
    dispatcher.startup.register(on_startup)

    dispatcher.include_router(my_router)

    app = Application()
    app["bot"] = bot

    app.router.add_get("/demo", demo_handler)
    app.router.add_post("/demo/checkData", check_data_handler)
    app.router.add_post("/demo/sendMessage", send_message_handler)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app, path="/webhook")
    setup_application(app, dispatcher, bot=bot)

    run_app(app, host="127.0.0.1", port=8081)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
