from aiogram.methods import RestrictChatMember
from aiogram.types import ChatPermissions
from tests.mocked_bot import MockedBot


class TestRestrictChatMember:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RestrictChatMember, ok=True, result=True)

        response: bool = await bot.restrict_chat_member(
            chat_id=-42, user_id=42, permissions=ChatPermissions()
        )
        bot.get_request()
        assert response == prepare_result.result
