from aiogram.methods import DeleteWebhook, Request
from tests.mocked_bot import MockedBot


class TestDeleteWebhook:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteWebhook, ok=True, result=True)

        response: bool = await DeleteWebhook()
        request: Request = bot.get_request()
        assert request.method == "deleteWebhook"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteWebhook, ok=True, result=True)

        response: bool = await bot.delete_webhook()
        request: Request = bot.get_request()
        assert request.method == "deleteWebhook"
        assert response == prepare_result.result
