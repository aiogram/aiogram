import pytest
from aiogram.api.methods import Request, SendAudio
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendAudio:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendAudio, ok=True, result=None)

        response: Message = await SendAudio(
            chat_id=..., audio=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendAudio"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendAudio, ok=True, result=None)

        response: Message = await bot.send_audio(
            chat_id=..., audio=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendAudio"
        # assert request.data == {}
        assert response == prepare_result.result
