import datetime

import pytest

from aiogram.methods import Request, SendPhoto
from aiogram.types import Chat, Message, PhotoSize
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSendPhoto:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendPhoto,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                photo=[
                    PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                ],
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendPhoto(chat_id=42, photo="file id")
        request: Request = bot.get_request()
        assert request.method == "sendPhoto"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendPhoto,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                photo=[
                    PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                ],
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_photo(chat_id=42, photo="file id")
        request: Request = bot.get_request()
        assert request.method == "sendPhoto"
        assert response == prepare_result.result
