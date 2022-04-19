import pytest

from aiogram.methods import DeclineChatJoinRequest, Request
from tests.mocked_bot import MockedBot


class TestDeclineChatJoinRequest:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeclineChatJoinRequest, ok=True, result=True)

        response: bool = await DeclineChatJoinRequest(
            chat_id=-42,
            user_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "declineChatJoinRequest"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeclineChatJoinRequest, ok=True, result=True)

        response: bool = await bot.decline_chat_join_request(
            chat_id=-42,
            user_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "declineChatJoinRequest"
        assert response == prepare_result.result
