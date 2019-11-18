import pytest
from aiogram.api.methods import Request, SendVideo
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendVideo:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVideo, ok=True, result=None)

        response: Message = await SendVideo(
            chat_id=..., video=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideo"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVideo, ok=True, result=None)

        response: Message = await bot.send_video(
            chat_id=..., video=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideo"
        # assert request.data == {}
        assert response == prepare_result.result
