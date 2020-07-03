import datetime

import pytest

from aiogram.api.methods import ForwardMessage, Request
from aiogram.api.types import Chat, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestForwardMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            ForwardMessage,
            ok=True,
            result=MessageFactory(
            ),
        )

        response: Message = await ForwardMessage(
            chat_id=private_chat.id, from_chat_id=private_chat.id, message_id=42
        )
        request: Request = bot.get_request()
        assert request.method == "forwardMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            ForwardMessage,
            ok=True,
            result=MessageFactory(
            ),
        )

        response: Message = await bot.forward_message(
            chat_id=private_chat.id, from_chat_id=private_chat.id, message_id=42
        )
        request: Request = bot.get_request()
        assert request.method == "forwardMessage"
        # assert request.data == {}
        assert response == prepare_result.result
