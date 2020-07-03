import datetime

import pytest

from aiogram.api.methods import Request, SendLocation
from aiogram.api.types import Chat, Location, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendLocation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendLocation,
            ok=True,
            result=MessageFactory(location=Location(longitude=3.14, latitude=3.14)),
        )

        response: Message = await SendLocation(
            chat_id=private_chat.id, latitude=3.14, longitude=3.14
        )
        request: Request = bot.get_request()
        assert request.method == "sendLocation"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendLocation,
            ok=True,
            result=MessageFactory(location=Location(longitude=3.14, latitude=3.14)),
        )

        response: Message = await bot.send_location(
            chat_id=private_chat.id, latitude=3.14, longitude=3.14
        )
        request: Request = bot.get_request()
        assert request.method == "sendLocation"
        assert response == prepare_result.result
