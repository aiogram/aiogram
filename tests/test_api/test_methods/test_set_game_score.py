import pytest
from aiogram.api.methods import Request, SetGameScore
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetGameScore:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetGameScore, ok=True, result=None)

        response: Union[Message, bool] = await SetGameScore(
            user_id=..., score=...,
        )
        request: Request = bot.get_request()
        assert request.method == "setGameScore"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetGameScore, ok=True, result=None)

        response: Union[Message, bool] = await bot.set_game_score(
            user_id=..., score=...,
        )
        request: Request = bot.get_request()
        assert request.method == "setGameScore"
        # assert request.data == {}
        assert response == prepare_result.result
