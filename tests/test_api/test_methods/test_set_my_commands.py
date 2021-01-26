import pytest

from aiogram.methods import Request, SetMyCommands
from aiogram.types import BotCommand
from tests.mocked_bot import MockedBot


class TestSetMyCommands:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyCommands, ok=True, result=None)

        response: bool = await SetMyCommands(
            commands=[BotCommand(command="command", description="Bot command")],
        )
        request: Request = bot.get_request()
        assert request.method == "setMyCommands"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyCommands, ok=True, result=None)

        response: bool = await bot.set_my_commands(
            commands=[],
        )
        request: Request = bot.get_request()
        assert request.method == "setMyCommands"
        # assert request.data == {}
        assert response == prepare_result.result
