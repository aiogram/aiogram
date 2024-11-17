from aiogram.methods import DeleteMyCommands
from tests.mocked_bot import MockedBot


class TestKickChatMember:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteMyCommands, ok=True, result=True)

        response: bool = await bot.delete_my_commands()
        request = bot.get_request()
        assert response == prepare_result.result
