from aiogram.methods import SetChatMemberTag
from tests.mocked_bot import MockedBot


class TestSetChatMemberTag:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatMemberTag, ok=True, result=True)

        response: bool = await bot.set_chat_member_tag(chat_id=-42, user_id=42, tag="test")
        bot.get_request()
        assert response == prepare_result.result
