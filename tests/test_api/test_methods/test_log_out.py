import pytest

from aiogram.methods import LogOut, Request
from tests.mocked_bot import MockedBot


class TestLogOut:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(LogOut, ok=True, result=True)

        response: bool = await LogOut()
        request: Request = bot.get_request()
        assert request.method == "logOut"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(LogOut, ok=True, result=True)

        response: bool = await bot.log_out()
        request: Request = bot.get_request()
        assert request.method == "logOut"
        # assert request.data == {}
        assert response == prepare_result.result
