import pytest
from aiogram.api.methods import PinChatMessage, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestPinChatMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PinChatMessage, ok=True, result=None)

        response: bool = await PinChatMessage(
            chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "pinChatMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PinChatMessage, ok=True, result=None)

        response: bool = await bot.pin_chat_message(
            chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "pinChatMessage"
        # assert request.data == {}
        assert response == prepare_result.result
