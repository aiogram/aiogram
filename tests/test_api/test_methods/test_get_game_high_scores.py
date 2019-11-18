import pytest
from aiogram.api.methods import GetGameHighScores, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetGameHighScores:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetGameHighScores, ok=True, result=None)

        response: List[GameHighScore] = await GetGameHighScores(user_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getGameHighScores"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetGameHighScores, ok=True, result=None)

        response: List[GameHighScore] = await bot.get_game_high_scores(user_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getGameHighScores"
        # assert request.data == {}
        assert response == prepare_result.result
