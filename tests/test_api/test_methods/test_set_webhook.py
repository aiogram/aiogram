import pytest

from aiogram.api.methods import Request, SetWebhook
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetWebhook:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetWebhook, ok=True, result=None)

        response: bool = await SetWebhook(url=...)
        request: Request = bot.get_request()
        assert request.method == "setWebhook"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetWebhook, ok=True, result=None)

        response: bool = await bot.set_webhook(url=...)
        request: Request = bot.get_request()
        assert request.method == "setWebhook"
        # assert request.data == {}
        assert response == prepare_result.result
