import pytest

from aiogram.methods import GetMe, Request
from aiogram.types import User
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestGetMe:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=False, first_name="User")
        )

        response: User = await GetMe()
        request: Request = bot.get_request()
        assert request.method == "getMe"
        assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=False, first_name="User")
        )
        response: User = await bot.get_me()
        request: Request = bot.get_request()
        assert request.method == "getMe"
        assert request.data == {}
        assert response == prepare_result.result

    async def test_me_property(self, bot: MockedBot):
        response: User = await bot.me()
        assert isinstance(response, User)
        assert response == bot._me
