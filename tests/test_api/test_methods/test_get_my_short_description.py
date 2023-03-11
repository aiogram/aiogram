from aiogram.methods import GetMyShortDescription, Request
from aiogram.types import BotShortDescription
from tests.mocked_bot import MockedBot


class TestGetMyShortDescription:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMyShortDescription, ok=True, result=BotShortDescription(short_description="Test")
        )

        response: BotShortDescription = await GetMyShortDescription()
        request: Request = bot.get_request()
        assert request.method == "getMyShortDescription"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMyShortDescription, ok=True, result=BotShortDescription(short_description="Test")
        )

        response: BotShortDescription = await bot.get_my_short_description()
        request: Request = bot.get_request()
        assert request.method == "getMyShortDescription"
        assert response == prepare_result.result
