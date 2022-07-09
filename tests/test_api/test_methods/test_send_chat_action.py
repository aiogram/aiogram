import pytest

from aiogram.methods import Request, SendChatAction
from aiogram.types import ChatAction
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSendChatAction:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=True)

        response: bool = await SendChatAction(chat_id=42, action="typing")
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=True)

        response: bool = await bot.send_chat_action(chat_id=42, action="typing")
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        assert response == prepare_result.result

    async def test_chat_action_class(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=True)

        response: bool = await bot.send_chat_action(chat_id=42, action=ChatAction.TYPING)
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        assert request.data["action"] == "typing"
        assert response == prepare_result.result
