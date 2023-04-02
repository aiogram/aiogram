from aiogram.methods import GetChatMemberCount, Request
from tests.mocked_bot import MockedBot


class TestGetChatMembersCount:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMemberCount, ok=True, result=42)

        response: int = await bot.get_chat_member_count(chat_id=-42)
        request = bot.get_request()
        assert response == prepare_result.result
