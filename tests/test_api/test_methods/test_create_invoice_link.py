import pytest

from aiogram.methods import CreateInvoiceLink, Request
from aiogram.types import LabeledPrice
from tests.mocked_bot import MockedBot


class TestCreateInvoiceLink:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CreateInvoiceLink, ok=True, result="https://t.me/invoice/example"
        )

        response: str = await CreateInvoiceLink(
            title="test",
            description="test",
            payload="test",
            provider_token="test",
            currency="BTC",
            prices=[LabeledPrice(label="Test", amount=1)],
        )
        request: Request = bot.get_request()
        assert request.method == "createInvoiceLink"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CreateInvoiceLink, ok=True, result="https://t.me/invoice/example"
        )

        response: str = await bot.create_invoice_link(
            title="test",
            description="test",
            payload="test",
            provider_token="test",
            currency="BTC",
            prices=[LabeledPrice(label="Test", amount=1)],
        )
        request: Request = bot.get_request()
        assert request.method == "createInvoiceLink"
        assert response == prepare_result.result
