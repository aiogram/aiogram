from aiogram.methods import Request, SetWebhook
from tests.mocked_bot import MockedBot


class TestSetWebhook:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetWebhook, ok=True, result=True)

        response: bool = await SetWebhook(url="https://example.com")
        request: Request = bot.get_request()
        assert request.method == "setWebhook"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetWebhook, ok=True, result=True)

        response: bool = await bot.set_webhook(url="https://example.com")
        request: Request = bot.get_request()
        assert request.method == "setWebhook"
        assert response == prepare_result.result
