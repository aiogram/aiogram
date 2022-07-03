import pytest

from aiogram.methods import BanChatSenderChat, Request
from tests.mocked_bot import MockedBot


class TestBanChatSenderChat:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(BanChatSenderChat, ok=True, result=True)

        response: bool = await BanChatSenderChat(
            chat_id=-42,
            sender_chat_id=-1337,
        )
        request: Request = bot.get_request()
        assert request.method == "banChatSenderChat"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(BanChatSenderChat, ok=True, result=True)

        response: bool = await bot.ban_chat_sender_chat(
            chat_id=-42,
            sender_chat_id=-1337,
        )
        request: Request = bot.get_request()
        assert request.method == "banChatSenderChat"
        # assert request.data == {}
        assert response == prepare_result.result
