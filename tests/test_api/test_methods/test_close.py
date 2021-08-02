import pytest

from aiogram.methods import Close, Request
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestClose:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(Close, ok=True, result=True)

        response: bool = await Close()
        request: Request = bot.get_request()
        assert request.method == "close"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(Close, ok=True, result=True)

        response: bool = await bot.close()
        request: Request = bot.get_request()
        assert request.method == "close"
        # assert request.data == {}
        assert response == prepare_result.result
