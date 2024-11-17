from typing import List

from aiogram.methods import GetMyCommands
from aiogram.types import BotCommand
from tests.mocked_bot import MockedBot


class TestGetMyCommands:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetMyCommands, ok=True, result=None)

        response: List[BotCommand] = await bot.get_my_commands()
        request = bot.get_request()
        assert response == prepare_result.result
