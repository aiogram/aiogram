import pytest

from aiogram.api.methods import Request, UnbanChatSenderChat
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestUnbanChatSenderChat:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatSenderChat, ok=True, result=None)

        response: bool = await UnbanChatSenderChat(
            chat_id=...,
            sender_chat_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "unbanChatSenderChat"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatSenderChat, ok=True, result=None)

        response: bool = await bot.unban_chat_sender_chat(
            chat_id=...,
            sender_chat_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "unbanChatSenderChat"
        # assert request.data == {}
        assert response == prepare_result.result
