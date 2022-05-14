import datetime

import pytest

from aiogram.methods import Request, SendMessage
from aiogram.types import Chat, ForceReply, Message
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSendMessage:
    async def test_method(self, bot: MockedBot):
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

        response: Message = await SendMessage(chat_id=42, text="test")
        request: Request = bot.get_request()
        assert request.method == "sendMessage"
        assert response == prepare_result.result

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
        request: Request = bot.get_request()
        assert request.method == "sendMessage"
        assert response == prepare_result.result

    async def test_force_reply(self):
        # https://github.com/aiogram/aiogram/issues/901
        method = SendMessage(text="test", chat_id=42, reply_markup=ForceReply())
        assert isinstance(method.reply_markup, ForceReply)
