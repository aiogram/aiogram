import pytest

from aiogram.methods import Request, SetChatAdministratorCustomTitle
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSetChatTitle:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatAdministratorCustomTitle, ok=True, result=True)

        response: bool = await SetChatAdministratorCustomTitle(
            chat_id=-42, user_id=42, custom_title="test chat"
        )
        request: Request = bot.get_request()
        assert request.method == "setChatAdministratorCustomTitle"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatAdministratorCustomTitle, ok=True, result=True)

        response: bool = await bot.set_chat_administrator_custom_title(
            chat_id=-42, user_id=42, custom_title="test chat"
        )
        request: Request = bot.get_request()
        assert request.method == "setChatAdministratorCustomTitle"
        assert response == prepare_result.result
