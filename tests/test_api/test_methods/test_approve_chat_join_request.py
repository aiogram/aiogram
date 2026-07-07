from aiogram.methods import ApproveChatJoinRequest
from tests.mocked_bot import MockedBot


class TestApproveChatJoinRequest:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ApproveChatJoinRequest, ok=True, result=None)

        response: bool = await bot.approve_chat_join_request(
            chat_id=-42,
            user_id=42,
        )
        bot.get_request()
        assert response == prepare_result.result
