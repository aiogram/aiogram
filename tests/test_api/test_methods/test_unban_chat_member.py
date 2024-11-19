from aiogram.methods import UnbanChatMember
from tests.mocked_bot import MockedBot


class TestUnbanChatMember:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatMember, ok=True, result=True)

        response: bool = await bot.unban_chat_member(chat_id=-42, user_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
