from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.handler import MessageHandler

TOKEN = "42:TOKEN"
dp = Dispatcher()


@dp.message(commands=["start"])
class MyHandler(MessageHandler):
    """
    This handler receive messages with `/start` command

    Usage of Class-based handlers
    """

    async def handle(self) -> Any:
        await self.event.answer(f"<b>Hello, {self.from_user.full_name}!</b>")


@dp.message(content_types=[types.ContentType.ANY])
async def echo_handler(message: types.Message, bot: Bot) -> Any:
    """
    Handler will forward received message back to the sender

    Usage of Function-based handlers
    """

    await bot.forward_message(
        from_chat_id=message.chat.id, chat_id=message.chat.id, message_id=message.message_id
    )


def main() -> None:
    bot = Bot(TOKEN, parse_mode="HTML")
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
