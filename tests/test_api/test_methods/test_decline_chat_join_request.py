from aiogram.methods import DeclineChatJoinRequest
from tests.mocked_bot import MockedBot


class TestDeclineChatJoinRequest:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeclineChatJoinRequest, ok=True, result=True)

        response: bool = await bot.decline_chat_join_request(
            chat_id=-42,
            user_id=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
