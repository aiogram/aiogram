import pytest

from aiogram.api.methods import GetChatMember, Request
from aiogram.api.types import ChatMember
from tests.factories.user import UserFactory
from tests.mocked_bot import MockedBot


class TestGetChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatMember, ok=True, result=ChatMember(status="creator"),
        )

        response: ChatMember = await GetChatMember(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "getChatMember"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatMember, ok=True, result=ChatMember(status="creator"),
        )

        response: ChatMember = await bot.get_chat_member(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "getChatMember"
        assert response == prepare_result.result
