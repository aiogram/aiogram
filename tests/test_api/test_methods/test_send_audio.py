import datetime

import pytest

from aiogram.api.methods import Request, SendAudio
from aiogram.api.types import Audio, Chat, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendAudio:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendAudio,
            ok=True,
            result=MessageFactory(
                audio=Audio(file_id="file id", duration=42, file_unique_id="file id"),
            ),
        )

        response: Message = await SendAudio(chat_id=private_chat.id, audio="file id")
        request: Request = bot.get_request()
        assert request.method == "sendAudio"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendAudio,
            ok=True,
            result=MessageFactory(
                audio=Audio(file_id="file id", duration=42, file_unique_id="file id"),
            ),
        )

        response: Message = await bot.send_audio(chat_id=private_chat.id, audio="file id")
        request: Request = bot.get_request()
        assert request.method == "sendAudio"
        assert response == prepare_result.result
