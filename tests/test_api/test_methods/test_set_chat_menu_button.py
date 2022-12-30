from aiogram.methods import Request, SetChatMenuButton
from tests.mocked_bot import MockedBot


class TestSetChatMenuButton:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatMenuButton, ok=True, result=True)

        response: bool = await SetChatMenuButton()
        request: Request = bot.get_request()
        assert request.method == "setChatMenuButton"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatMenuButton, ok=True, result=True)

        response: bool = await bot.set_chat_menu_button()
        request: Request = bot.get_request()
        assert request.method == "setChatMenuButton"
        # assert request.data == {}
        assert response == prepare_result.result
