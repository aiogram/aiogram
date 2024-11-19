from typing import List

from aiogram.methods import GetUpdates
from aiogram.types import Update
from tests.mocked_bot import MockedBot


class TestGetUpdates:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUpdates, ok=True, result=[Update(update_id=42)])

        response: List[Update] = await bot.get_updates()
        request = bot.get_request()
        assert response == prepare_result.result
