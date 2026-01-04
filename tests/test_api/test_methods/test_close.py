from aiogram.methods import Close
from tests.mocked_bot import MockedBot


class TestClose:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(Close, ok=True, result=True)

        response: bool = await bot.close()
        bot.get_request()
        assert response == prepare_result.result
