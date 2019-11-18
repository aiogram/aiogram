import pytest
from aiogram.api.methods import GetUpdates, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetUpdates:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUpdates, ok=True, result=None)

        response: List[Update] = await GetUpdates()
        request: Request = bot.get_request()
        assert request.method == "getUpdates"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUpdates, ok=True, result=None)

        response: List[Update] = await bot.get_updates()
        request: Request = bot.get_request()
        assert request.method == "getUpdates"
        # assert request.data == {}
        assert response == prepare_result.result
