from aiogram.methods import GetMyShortDescription
from aiogram.types import BotShortDescription
from tests.mocked_bot import MockedBot


class TestGetMyShortDescription:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMyShortDescription, ok=True, result=BotShortDescription(short_description="Test")
        )

        response: BotShortDescription = await bot.get_my_short_description()
        request = bot.get_request()
        assert response == prepare_result.result
