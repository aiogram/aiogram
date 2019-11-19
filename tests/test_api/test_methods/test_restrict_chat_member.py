import pytest

from aiogram.api.methods import Request, RestrictChatMember
from aiogram.api.types import ChatPermissions
from tests.mocked_bot import MockedBot


class TestRestrictChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RestrictChatMember, ok=True, result=True)

        response: bool = await RestrictChatMember(
            chat_id=-42, user_id=42, permissions=ChatPermissions()
        )
        request: Request = bot.get_request()
        assert request.method == "restrictChatMember"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RestrictChatMember, ok=True, result=True)

        response: bool = await bot.restrict_chat_member(
            chat_id=-42, user_id=42, permissions=ChatPermissions()
        )
        request: Request = bot.get_request()
        assert request.method == "restrictChatMember"
        assert response == prepare_result.result
