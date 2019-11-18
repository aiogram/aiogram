import pytest
from aiogram.api.methods import Request, SendContact
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendContact:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendContact, ok=True, result=None)

        response: Message = await SendContact(
            chat_id=..., phone_number=..., first_name=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendContact"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendContact, ok=True, result=None)

        response: Message = await bot.send_contact(
            chat_id=..., phone_number=..., first_name=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendContact"
        # assert request.data == {}
        assert response == prepare_result.result
