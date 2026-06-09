from aiogram.methods import BanChatMember
from tests.mocked_bot import MockedBot


class TestKickChatMember:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(BanChatMember, ok=True, result=True)

        response: bool = await bot.ban_chat_member(chat_id=-42, user_id=42)
        bot.get_request()
        assert response == prepare_result.result
