import pytest

from aiogram.api.methods import Request, UnbanChatMember
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestUnbanChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatMember, ok=True, result=None)

        response: bool = await UnbanChatMember(chat_id=..., user_id=...)
        request: Request = bot.get_request()
        assert request.method == "unbanChatMember"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatMember, ok=True, result=None)

        response: bool = await bot.unban_chat_member(chat_id=..., user_id=...)
        request: Request = bot.get_request()
        assert request.method == "unbanChatMember"
        # assert request.data == {}
        assert response == prepare_result.result
