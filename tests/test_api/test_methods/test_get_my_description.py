from aiogram.methods import GetMyDescription
from aiogram.types import BotDescription
from tests.mocked_bot import MockedBot


class TestGetMyDescription:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMyDescription, ok=True, result=BotDescription(description="Test")
        )

        response: BotDescription = await bot.get_my_description()
        request = bot.get_request()
        assert response == prepare_result.result
