from aiogram.methods import GetMyName
from aiogram.types import BotName
from tests.mocked_bot import MockedBot


class TestGetMyName:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetMyName, ok=True, result=BotName(name="Test"))

        response: BotName = await bot.get_my_name()
        assert response == prepare_result.result
