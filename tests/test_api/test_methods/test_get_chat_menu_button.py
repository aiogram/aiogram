from aiogram.methods import GetChatMenuButton
from aiogram.types import MenuButton, MenuButtonDefault
from tests.mocked_bot import MockedBot


class TestGetChatMenuButton:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatMenuButton, ok=True, result=MenuButtonDefault())

        response: MenuButton = await bot.get_chat_menu_button()
        request = bot.get_request()
        assert response == prepare_result.result
