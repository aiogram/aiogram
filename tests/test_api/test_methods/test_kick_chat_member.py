import pytest

from aiogram.methods import KickChatMember, Request
from tests.mocked_bot import MockedBot


class TestKickChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(KickChatMember, ok=True, result=True)

        response: bool = await KickChatMember(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "kickChatMember"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(KickChatMember, ok=True, result=True)

        response: bool = await bot.kick_chat_member(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "kickChatMember"
        assert response == prepare_result.result
