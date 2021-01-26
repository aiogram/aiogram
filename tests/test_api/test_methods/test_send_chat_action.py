import pytest

from aiogram.methods import Request, SendChatAction
from tests.mocked_bot import MockedBot


class TestSendChatAction:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=True)

        response: bool = await SendChatAction(chat_id=42, action="typing")
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=True)

        response: bool = await bot.send_chat_action(chat_id=42, action="typing")
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        assert response == prepare_result.result
