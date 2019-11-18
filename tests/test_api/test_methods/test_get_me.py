import pytest

from aiogram.api.methods import GetMe, Request
from aiogram.api.types import User
from tests.mocked_bot import MockedBot


class TestGetMe:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=False, first_name="User")
        )

        response: User = await GetMe()
        request: Request = bot.get_request()
        assert request.method == "getMe"
        assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=False, first_name="User")
        )
        response: User = await bot.get_me()
        request: Request = bot.get_request()
        assert request.method == "getMe"
        assert request.data == {}
        assert response == prepare_result.result
