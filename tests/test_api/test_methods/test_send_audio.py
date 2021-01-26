import datetime

import pytest

from aiogram.methods import Request, SendAudio
from aiogram.types import Audio, Chat, File, Message
from tests.mocked_bot import MockedBot


class TestSendAudio:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendAudio,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                audio=Audio(file_id="file id", duration=42, file_unique_id="file id"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendAudio(chat_id=42, audio="file id")
        request: Request = bot.get_request()
        assert request.method == "sendAudio"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendAudio,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                audio=Audio(file_id="file id", duration=42, file_unique_id="file id"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_audio(chat_id=42, audio="file id")
        request: Request = bot.get_request()
        assert request.method == "sendAudio"
        assert response == prepare_result.result
