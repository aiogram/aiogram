import pytest

from aiogram.api.methods import ApproveChatJoinRequest, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestApproveChatJoinRequest:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ApproveChatJoinRequest, ok=True, result=None)

        response: bool = await ApproveChatJoinRequest(
            chat_id=...,
            user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "approveChatJoinRequest"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ApproveChatJoinRequest, ok=True, result=None)

        response: bool = await bot.approve_chat_join_request(
            chat_id=...,
            user_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "approveChatJoinRequest"
        # assert request.data == {}
        assert response == prepare_result.result
