import pytest
from aiogram.api.methods import GetChatMembersCount, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetChatMembersCount:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMembersCount, ok=True, result=None)

        response: int = await GetChatMembersCount(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getChatMembersCount"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMembersCount, ok=True, result=None)

        response: int = await bot.get_chat_members_count(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getChatMembersCount"
        # assert request.data == {}
        assert response == prepare_result.result
