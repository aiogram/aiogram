import pytest

from aiogram.methods import DeleteMyCommands, Request
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestKickChatMember:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteMyCommands, ok=True, result=True)

        response: bool = await DeleteMyCommands()
        request: Request = bot.get_request()
        assert request.method == "deleteMyCommands"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteMyCommands, ok=True, result=True)

        response: bool = await bot.delete_my_commands()
        request: Request = bot.get_request()
        assert request.method == "deleteMyCommands"
        assert response == prepare_result.result
