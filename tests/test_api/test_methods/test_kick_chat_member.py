import pytest
from aiogram.api.methods import KickChatMember, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestKickChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(KickChatMember, ok=True, result=None)

        response: bool = await KickChatMember(
            chat_id=..., user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "kickChatMember"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(KickChatMember, ok=True, result=None)

        response: bool = await bot.kick_chat_member(
            chat_id=..., user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "kickChatMember"
        # assert request.data == {}
        assert response == prepare_result.result
