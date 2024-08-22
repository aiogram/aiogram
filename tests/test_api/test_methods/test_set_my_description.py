from aiogram.methods import SetMyDescription
from tests.mocked_bot import MockedBot


class TestSetMyDescription:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyDescription, ok=True, result=True)

        response: bool = await bot.set_my_description(description="Test")
        request = bot.get_request()
        assert response == prepare_result.result
