import datetime

import pytest

from aiogram.methods import Request, SendLocation
from aiogram.types import Chat, Location, Message
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSendLocation:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendLocation,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                location=Location(longitude=3.14, latitude=3.14),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendLocation(chat_id=42, latitude=3.14, longitude=3.14)
        request: Request = bot.get_request()
        assert request.method == "sendLocation"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendLocation,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                location=Location(longitude=3.14, latitude=3.14),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_location(chat_id=42, latitude=3.14, longitude=3.14)
        request: Request = bot.get_request()
        assert request.method == "sendLocation"
        assert response == prepare_result.result
