from typing import List

import pytest

from aiogram.methods import GetUpdates, Request
from aiogram.types import Update
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestGetUpdates:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUpdates, ok=True, result=[Update(update_id=42)])

        response: List[Update] = await GetUpdates()
        request: Request = bot.get_request()
        assert request.method == "getUpdates"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUpdates, ok=True, result=[Update(update_id=42)])

        response: List[Update] = await bot.get_updates()
        request: Request = bot.get_request()
        assert request.method == "getUpdates"
        assert response == prepare_result.result
