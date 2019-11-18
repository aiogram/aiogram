import pytest
from aiogram.api.methods import Request, RestrictChatMember
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestRestrictChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RestrictChatMember, ok=True, result=None)

        response: bool = await RestrictChatMember(
            chat_id=..., user_id=..., permissions=...,
        )
        request: Request = bot.get_request()
        assert request.method == "restrictChatMember"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RestrictChatMember, ok=True, result=None)

        response: bool = await bot.restrict_chat_member(
            chat_id=..., user_id=..., permissions=...,
        )
        request: Request = bot.get_request()
        assert request.method == "restrictChatMember"
        # assert request.data == {}
        assert response == prepare_result.result
