from datetime import datetime

from aiogram import Dispatcher, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot

issue_router = Router()


@issue_router.message(Command("test"))
async def my_handler(message: Message):
    await message.answer("PASS")
    return True


async def test_something(bot: MockedBot):
    dp = Dispatcher()
    dp.include_router(issue_router)
    bot.add_result_for(method=SendMessage, ok=True)
    chat = Chat(id=666, type=ChatType.PRIVATE)
    user = User(id=666, is_bot=False, first_name="User")
    msg = Message(message_id=1, date=datetime.now(), from_user=user, chat=chat, text="/test")
    result = await dp.feed_update(bot, Update(message=msg, update_id=1))
    assert result is True
