from aiogram.methods import GetChatMember
from aiogram.types import ChatMemberOwner, User
from tests.mocked_bot import MockedBot


class TestGetChatMember:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatMember,
            ok=True,
            result=ChatMemberOwner(
                user=User(id=42, is_bot=False, first_name="User"), is_anonymous=False
            ),
        )
        response = await bot.get_chat_member(chat_id=-42, user_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
