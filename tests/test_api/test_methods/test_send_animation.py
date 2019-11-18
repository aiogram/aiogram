import pytest
from aiogram.api.methods import Request, SendAnimation
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendAnimation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendAnimation, ok=True, result=None)

        response: Message = await SendAnimation(
            chat_id=..., animation=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendAnimation"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendAnimation, ok=True, result=None)

        response: Message = await bot.send_animation(
            chat_id=..., animation=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendAnimation"
        # assert request.data == {}
        assert response == prepare_result.result
