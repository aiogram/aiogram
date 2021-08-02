import pytest

from aiogram.methods import PromoteChatMember, Request
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestPromoteChatMember:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PromoteChatMember, ok=True, result=True)

        response: bool = await PromoteChatMember(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "promoteChatMember"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PromoteChatMember, ok=True, result=True)

        response: bool = await bot.promote_chat_member(chat_id=-42, user_id=42)
        request: Request = bot.get_request()
        assert request.method == "promoteChatMember"
        assert response == prepare_result.result
