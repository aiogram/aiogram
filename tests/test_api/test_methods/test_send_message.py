import datetime

from aiogram.methods import SendMessage
from aiogram.types import Chat, ForceReply, Message, ReplyKeyboardRemove
from tests.mocked_bot import MockedBot


class TestSendMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendMessage,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="test",
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_message(chat_id=42, text="test")
        request = bot.get_request()
        assert response == prepare_result.result

    async def test_force_reply(self):
        # https://github.com/aiogram/aiogram/issues/901
        method = SendMessage(text="test", chat_id=42, reply_markup=ForceReply())
        assert isinstance(method.reply_markup, ForceReply)

    async def test_reply_keyboard_remove(self):
        # https://github.com/aiogram/aiogram/issues/901
        method = SendMessage(text="test", chat_id=42, reply_markup=ReplyKeyboardRemove())
        assert isinstance(method.reply_markup, ReplyKeyboardRemove)
