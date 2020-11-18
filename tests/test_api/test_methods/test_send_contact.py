import datetime

import pytest

from aiogram.methods import Request, SendContact
from aiogram.types import Chat, Contact, Message
from tests.mocked_bot import MockedBot


class TestSendContact:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendContact,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                contact=Contact(phone_number="911", first_name="911"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendContact(chat_id=42, phone_number="911", first_name="911")
        request: Request = bot.get_request()
        assert request.method == "sendContact"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendContact,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                contact=Contact(phone_number="911", first_name="911"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_contact(
            chat_id=42, phone_number="911", first_name="911"
        )
        request: Request = bot.get_request()
        assert request.method == "sendContact"
        assert response == prepare_result.result
