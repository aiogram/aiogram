import pytest

from aiogram.methods import PinChatMessage, Request
from tests.mocked_bot import MockedBot


class TestPinChatMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PinChatMessage, ok=True, result=True)

        response: bool = await PinChatMessage(chat_id=-42, message_id=42)
        request: Request = bot.get_request()
        assert request.method == "pinChatMessage"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PinChatMessage, ok=True, result=True)

        response: bool = await bot.pin_chat_message(chat_id=-42, message_id=42)
        request: Request = bot.get_request()
        assert request.method == "pinChatMessage"
        assert response == prepare_result.result
