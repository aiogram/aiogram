import pytest

from aiogram.api.methods import Request, SendInvoice
from aiogram.api.types import Chat, Invoice, LabeledPrice, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendInvoice:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendInvoice,
            ok=True,
            result=MessageFactory(
                invoice=Invoice(
                    title="test",
                    description="test",
                    start_parameter="brilliant",
                    currency="BTC",
                    total_amount=1,
                )
            ),
        )

        response: Message = await SendInvoice(
            chat_id=private_chat.id,
            title="test",
            description="test",
            payload="payload",
            provider_token="TEST:token",
            start_parameter="brilliant",
            currency="BTC",
            prices=[LabeledPrice(amount=1, label="test")],
        )
        request: Request = bot.get_request()
        assert request.method == "sendInvoice"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendInvoice,
            ok=True,
            result=MessageFactory(
                invoice=Invoice(
                    title="test",
                    description="test",
                    start_parameter="brilliant",
                    currency="BTC",
                    total_amount=1,
                )
            ),
        )

        response: Message = await bot.send_invoice(
            chat_id=private_chat.id,
            title="test",
            description="test",
            payload="payload",
            provider_token="TEST:token",
            start_parameter="brilliant",
            currency="BTC",
            prices=[LabeledPrice(amount=1, label="test")],
        )
        request: Request = bot.get_request()
        assert request.method == "sendInvoice"
        assert response == prepare_result.result
