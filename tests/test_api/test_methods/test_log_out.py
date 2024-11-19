from aiogram.methods import LogOut
from tests.mocked_bot import MockedBot


class TestLogOut:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(LogOut, ok=True, result=True)

        response: bool = await bot.log_out()
        request = bot.get_request()
        assert response == prepare_result.result
