from typing import List

import pytest

from aiogram.api.methods import GetChatAdministrators, Request
from aiogram.api.types import ChatMember, User
from tests.mocked_bot import MockedBot


class TestGetChatAdministrators:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatAdministrators,
            ok=True,
            result=[
                ChatMember(user=User(id=42, is_bot=False, first_name="User"), status="creator")
            ],
        )

        response: List[ChatMember] = await GetChatAdministrators(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "getChatAdministrators"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatAdministrators,
            ok=True,
            result=[
                ChatMember(user=User(id=42, is_bot=False, first_name="User"), status="creator")
            ],
        )
        response: List[ChatMember] = await bot.get_chat_administrators(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "getChatAdministrators"
        assert response == prepare_result.result
