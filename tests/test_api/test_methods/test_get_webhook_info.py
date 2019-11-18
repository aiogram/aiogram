import pytest

from aiogram.api.methods import GetWebhookInfo, Request
from aiogram.api.types import WebhookInfo
from tests.mocked_bot import MockedBot


class TestGetWebhookInfo:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetWebhookInfo,
            ok=True,
            result=WebhookInfo(
                url="https://example.com", has_custom_certificate=False, pending_update_count=0
            ),
        )

        response: WebhookInfo = await GetWebhookInfo()
        request: Request = bot.get_request()
        assert request.method == "getWebhookInfo"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetWebhookInfo,
            ok=True,
            result=WebhookInfo(
                url="https://example.com", has_custom_certificate=False, pending_update_count=0
            ),
        )

        response: WebhookInfo = await bot.get_webhook_info()
        request: Request = bot.get_request()
        assert request.method == "getWebhookInfo"
        assert response == prepare_result.result
