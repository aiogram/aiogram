import pytest
from aiogram.api.methods import LeaveChat, Request
from tests.mocked_bot import MockedBot


class TestLeaveChat:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(LeaveChat, ok=True, result=True)

        response: bool = await LeaveChat(chat_id=-42,)
        request: Request = bot.get_request()
        assert request.method == "leaveChat"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(LeaveChat, ok=True, result=True)

        response: bool = await bot.leave_chat(chat_id=-42,)
        request: Request = bot.get_request()
        assert request.method == "leaveChat"
        assert response == prepare_result.result
