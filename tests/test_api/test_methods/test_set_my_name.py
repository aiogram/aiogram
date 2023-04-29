from aiogram.methods import SetMyName
from tests.mocked_bot import MockedBot


class TestSetMyName:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyName, ok=True, result=True)

        response: bool = await bot.set_my_name()
        assert response == prepare_result.result
