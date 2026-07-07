from aiogram.methods import SetMyShortDescription
from tests.mocked_bot import MockedBot


class TestSetMyShortDescription:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyShortDescription, ok=True, result=True)

        response: bool = await bot.set_my_short_description(short_description="Test")
        bot.get_request()
        assert response == prepare_result.result
