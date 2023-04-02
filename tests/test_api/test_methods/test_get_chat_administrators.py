from typing import List

from aiogram.methods import GetChatAdministrators, Request
from aiogram.types import ChatMember, ChatMemberOwner, User
from tests.mocked_bot import MockedBot


class TestGetChatAdministrators:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatAdministrators,
            ok=True,
            result=[
                ChatMemberOwner(
                    user=User(id=42, is_bot=False, first_name="User"), is_anonymous=False
                )
            ],
        )
        response: List[ChatMember] = await bot.get_chat_administrators(chat_id=-42)
        request = bot.get_request()
        assert response == prepare_result.result
