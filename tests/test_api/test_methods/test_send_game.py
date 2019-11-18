import pytest
from aiogram.api.methods import Request, SendGame
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendGame:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendGame, ok=True, result=None)

        response: Message = await SendGame(
            chat_id=..., game_short_name=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendGame"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendGame, ok=True, result=None)

        response: Message = await bot.send_game(
            chat_id=..., game_short_name=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendGame"
        # assert request.data == {}
        assert response == prepare_result.result
