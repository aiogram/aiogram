import datetime

import pytest

from aiogram.methods import Request, SendInvoice
from aiogram.types import Chat, Invoice, LabeledPrice, Message
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSendInvoice:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendInvoice,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                invoice=Invoice(
                    title="test",
                    description="test",
                    start_parameter="brilliant",
                    currency="BTC",
                    total_amount=1,
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendInvoice(
            chat_id=42,
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

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendInvoice,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                invoice=Invoice(
                    title="test",
                    description="test",
                    start_parameter="brilliant",
                    currency="BTC",
                    total_amount=1,
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_invoice(
            chat_id=42,
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
