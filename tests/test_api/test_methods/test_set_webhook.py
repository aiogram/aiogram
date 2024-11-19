from aiogram.methods import SetWebhook
from tests.mocked_bot import MockedBot


class TestSetWebhook:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetWebhook, ok=True, result=True)

        response: bool = await bot.set_webhook(url="https://example.com")
        request = bot.get_request()
        assert response == prepare_result.result
