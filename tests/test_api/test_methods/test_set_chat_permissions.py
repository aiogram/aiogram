import pytest

from aiogram.methods import Request, SetChatPermissions
from aiogram.types import ChatPermissions
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSetChatPermissions:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPermissions, ok=True, result=True)

        response: bool = await SetChatPermissions(
            chat_id=-42, permissions=ChatPermissions(can_send_messages=False)
        )
        request: Request = bot.get_request()
        assert request.method == "setChatPermissions"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPermissions, ok=True, result=True)

        response: bool = await bot.set_chat_permissions(
            chat_id=-42, permissions=ChatPermissions(can_send_messages=False)
        )
        request: Request = bot.get_request()
        assert request.method == "setChatPermissions"
        assert response == prepare_result.result
