from aiogram.methods import LeaveChat, Request
from tests.mocked_bot import MockedBot


class TestLeaveChat:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(LeaveChat, ok=True, result=True)

        response: bool = await bot.leave_chat(chat_id=-42)
        request = bot.get_request()
        assert response == prepare_result.result
