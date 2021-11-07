import pytest

from aiogram.api.methods import DeclineChatJoinRequest, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestDeclineChatJoinRequest:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeclineChatJoinRequest, ok=True, result=None)

        response: bool = await DeclineChatJoinRequest(
            chat_id=...,
            user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "declineChatJoinRequest"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeclineChatJoinRequest, ok=True, result=None)

        response: bool = await bot.decline_chat_join_request(
            chat_id=...,
            user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "declineChatJoinRequest"
        # assert request.data == {}
        assert response == prepare_result.result
