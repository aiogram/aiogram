import pytest

from aiogram.methods import GetChatMenuButton, Request
from aiogram.types import MenuButton
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetChatMenuButton:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMenuButton, ok=True, result=None)

        response: MenuButton = await GetChatMenuButton()
        request: Request = bot.get_request()
        assert request.method == "getChatMenuButton"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMenuButton, ok=True, result=None)

        response: MenuButton = await bot.get_chat_menu_button()
        request: Request = bot.get_request()
        assert request.method == "getChatMenuButton"
        # assert request.data == {}
        assert response == prepare_result.result
