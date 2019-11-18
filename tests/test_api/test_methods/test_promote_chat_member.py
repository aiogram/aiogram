import pytest
from aiogram.api.methods import PromoteChatMember, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestPromoteChatMember:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PromoteChatMember, ok=True, result=None)

        response: bool = await PromoteChatMember(
            chat_id=..., user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "promoteChatMember"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PromoteChatMember, ok=True, result=None)

        response: bool = await bot.promote_chat_member(
            chat_id=..., user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "promoteChatMember"
        # assert request.data == {}
        assert response == prepare_result.result
