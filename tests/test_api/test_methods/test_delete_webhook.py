import pytest
from aiogram.api.methods import DeleteWebhook, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestDeleteWebhook:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteWebhook, ok=True, result=None)

        response: bool = await DeleteWebhook()
        request: Request = bot.get_request()
        assert request.method == "deleteWebhook"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteWebhook, ok=True, result=None)

        response: bool = await bot.delete_webhook()
        request: Request = bot.get_request()
        assert request.method == "deleteWebhook"
        # assert request.data == {}
        assert response == prepare_result.result
