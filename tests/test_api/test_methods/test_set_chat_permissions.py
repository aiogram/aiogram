import pytest

from aiogram.api.methods import Request, SetChatPermissions
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetChatPermissions:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPermissions, ok=True, result=None)

        response: bool = await SetChatPermissions(chat_id=..., permissions=...)
        request: Request = bot.get_request()
        assert request.method == "setChatPermissions"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPermissions, ok=True, result=None)

        response: bool = await bot.set_chat_permissions(chat_id=..., permissions=...)
        request: Request = bot.get_request()
        assert request.method == "setChatPermissions"
        # assert request.data == {}
        assert response == prepare_result.result
