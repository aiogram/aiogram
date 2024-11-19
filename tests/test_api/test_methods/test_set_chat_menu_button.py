from aiogram.methods import SetChatMenuButton
from tests.mocked_bot import MockedBot


class TestSetChatMenuButton:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatMenuButton, ok=True, result=True)

        response: bool = await bot.set_chat_menu_button()
        request = bot.get_request()
        assert response == prepare_result.result
