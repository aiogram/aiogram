from aiogram.methods import ApproveChatJoinRequest, Request
from tests.mocked_bot import MockedBot


class TestApproveChatJoinRequest:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ApproveChatJoinRequest, ok=True, result=True)

        response: bool = await ApproveChatJoinRequest(
            chat_id=-42,
            user_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "approveChatJoinRequest"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ApproveChatJoinRequest, ok=True, result=None)

        response: bool = await bot.approve_chat_join_request(
            chat_id=-42,
            user_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "approveChatJoinRequest"
        assert response == prepare_result.result
