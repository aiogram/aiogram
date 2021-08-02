import pytest

from aiogram.methods import BanChatMember, Request
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestKickChatMember:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(BanChatMember, ok=True, result=True)

        response: bool = await BanChatMember(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "banChatMember"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(BanChatMember, ok=True, result=True)

        response: bool = await bot.ban_chat_member(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "banChatMember"
        assert response == prepare_result.result
