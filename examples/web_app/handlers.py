from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

my_router = Router()


@my_router.message(CommandStart())
async def command_start(message: Message, bot: Bot, base_url: str) -> None:
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(text="Open Menu", web_app=WebAppInfo(url=f"{base_url}/demo")),
    )
    await message.answer("""Hi!\nSend me any type of message to start.\nOr just send /webview""")


@my_router.message(Command("webview"))
async def command_webview(message: Message, base_url: str) -> None:
    await message.answer(
        "Good. Now you can try to send it via Webview",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Open Webview",
                        web_app=WebAppInfo(url=f"{base_url}/demo"),
                    ),
                ],
            ],
        ),
    )


@my_router.message(~F.message.via_bot)  # Echo to all messages except messages via bot
async def echo_all(message: Message, base_url: str) -> None:
    await message.answer(
        "Test webview",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Open", web_app=WebAppInfo(url=f"{base_url}/demo"))],
            ],
        ),
    )
