import pytest
from aiogram.api.methods import GetWebhookInfo, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetWebhookInfo:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetWebhookInfo, ok=True, result=None)

        response: WebhookInfo = await GetWebhookInfo()
        request: Request = bot.get_request()
        assert request.method == "getWebhookInfo"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetWebhookInfo, ok=True, result=None)

        response: WebhookInfo = await bot.get_webhook_info()
        request: Request = bot.get_request()
        assert request.method == "getWebhookInfo"
        # assert request.data == {}
        assert response == prepare_result.result
