import pytest
from aiogram.api.methods import GetChatMember, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMember, ok=True, result=None)

        response: ChatMember = await GetChatMember(
            chat_id=..., user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "getChatMember"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMember, ok=True, result=None)

        response: ChatMember = await bot.get_chat_member(
            chat_id=..., user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "getChatMember"
        # assert request.data == {}
        assert response == prepare_result.result
