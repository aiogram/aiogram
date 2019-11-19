import pytest

from aiogram.api.methods import Request, SendVoice
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendVoice:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVoice, ok=True, result=None)

        response: Message = await SendVoice(chat_id=..., voice=...)
        request: Request = bot.get_request()
        assert request.method == "sendVoice"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVoice, ok=True, result=None)

        response: Message = await bot.send_voice(chat_id=..., voice=...)
        request: Request = bot.get_request()
        assert request.method == "sendVoice"
        # assert request.data == {}
        assert response == prepare_result.result
