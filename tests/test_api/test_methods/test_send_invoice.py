import pytest

from aiogram.api.methods import Request, SendInvoice
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendInvoice:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendInvoice, ok=True, result=None)

        response: Message = await SendInvoice(
            chat_id=...,
            title=...,
            description=...,
            payload=...,
            provider_token=...,
            start_parameter=...,
            currency=...,
            prices=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendInvoice"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendInvoice, ok=True, result=None)

        response: Message = await bot.send_invoice(
            chat_id=...,
            title=...,
            description=...,
            payload=...,
            provider_token=...,
            start_parameter=...,
            currency=...,
            prices=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendInvoice"
        # assert request.data == {}
        assert response == prepare_result.result
