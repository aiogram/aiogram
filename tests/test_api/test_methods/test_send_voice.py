import datetime

import pytest
from aiogram.api.methods import Request, SendVoice
from aiogram.api.types import Chat, Message, Voice
from tests.mocked_bot import MockedBot


class TestSendVoice:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVoice,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                voice=Voice(file_id="file id", duration=0),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendVoice(chat_id=42, voice="file id")
        request: Request = bot.get_request()
        assert request.method == "sendVoice"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVoice,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                voice=Voice(file_id="file id", duration=0),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_voice(chat_id=42, voice="file id")
        request: Request = bot.get_request()
        assert request.method == "sendVoice"
        assert response == prepare_result.result
