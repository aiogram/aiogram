import datetime

import pytest

from aiogram.api.methods import Request, SendAnimation
from aiogram.api.types import Animation, Chat, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendAnimation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendAnimation,
            ok=True,
            result=MessageFactory(
                animation=Animation(
                    file_id="file id", width=42, height=42, duration=0, file_unique_id="file id"
                )
            ),
        )

        response: Message = await SendAnimation(chat_id=private_chat.id, animation="file id")
        request: Request = bot.get_request()
        assert request.method == "sendAnimation"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendAnimation,
            ok=True,
            result=MessageFactory(
                animation=Animation(
                    file_id="file id", width=42, height=42, duration=0, file_unique_id="file id"
                )
            ),
        )

        response: Message = await bot.send_animation(chat_id=private_chat.id, animation="file id")
        request: Request = bot.get_request()
        assert request.method == "sendAnimation"
        assert response == prepare_result.result
