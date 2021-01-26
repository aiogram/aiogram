import pytest

from aiogram.methods import GetMe, Request
from aiogram.types import User
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

    @pytest.mark.asyncio
    async def test_me_property(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=False, first_name="User")
        )

        response: User = await bot.me()
        request: Request = bot.get_request()

        assert isinstance(response, User)
        assert request.method == "getMe"
        assert request.data == {}
        assert response == prepare_result.result

        response2: User = await bot.me()
        assert response2 == response

        response3: User = await bot.me()
        assert response3 == response
        assert response2 == response3

        cache_info = bot.me.cache_info()
        assert cache_info.hits == 2
        assert cache_info.misses == 1
