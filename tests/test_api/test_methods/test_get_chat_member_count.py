from aiogram.methods import GetChatMemberCount, Request
from tests.mocked_bot import MockedBot


class TestGetChatMembersCount:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMemberCount, ok=True, result=42)

        response: int = await GetChatMemberCount(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "getChatMemberCount"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMemberCount, ok=True, result=42)

        response: int = await bot.get_chat_member_count(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "getChatMemberCount"
        assert response == prepare_result.result
