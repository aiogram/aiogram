from typing import List

import pytest

from aiogram.methods import GetMyCommands, Request
from aiogram.types import BotCommand
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestGetMyCommands:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetMyCommands, ok=True, result=None)

        response: List[BotCommand] = await GetMyCommands()
        request: Request = bot.get_request()
        assert request.method == "getMyCommands"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetMyCommands, ok=True, result=None)

        response: List[BotCommand] = await bot.get_my_commands()
        request: Request = bot.get_request()
        assert request.method == "getMyCommands"
        assert response == prepare_result.result
