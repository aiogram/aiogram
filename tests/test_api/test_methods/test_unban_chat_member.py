import pytest

from aiogram.methods import Request, UnbanChatMember
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestUnbanChatMember:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatMember, ok=True, result=True)

        response: bool = await UnbanChatMember(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "unbanChatMember"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatMember, ok=True, result=True)

        response: bool = await bot.unban_chat_member(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "unbanChatMember"
        assert response == prepare_result.result
