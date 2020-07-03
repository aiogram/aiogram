import pytest

from aiogram.api.methods import Request, SendContact
from aiogram.api.types import Chat, Contact, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendContact:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendContact,
            ok=True,
            result=MessageFactory(
                contact=Contact(phone_number="911", first_name="911"),
            ),
        )

        response: Message = await SendContact(
            chat_id=private_chat.id, phone_number="911", first_name="911"
        )
        request: Request = bot.get_request()
        assert request.method == "sendContact"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendContact,
            ok=True,
            result=MessageFactory(
                contact=Contact(phone_number="911", first_name="911"),
            ),
        )

        response: Message = await bot.send_contact(
            chat_id=private_chat.id, phone_number="911", first_name="911"
        )
        request: Request = bot.get_request()
        assert request.method == "sendContact"
        assert response == prepare_result.result
