from aiogram.methods import Request, SetMyDescription
from tests.mocked_bot import MockedBot


class TestSetMyDescription:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyDescription, ok=True, result=True)

        response: bool = await SetMyDescription(description="Test")
        request: Request = bot.get_request()
        assert request.method == "setMyDescription"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyDescription, ok=True, result=True)

        response: bool = await bot.set_my_description(description="Test")
        request: Request = bot.get_request()
        assert request.method == "setMyDescription"
        assert response == prepare_result.result
