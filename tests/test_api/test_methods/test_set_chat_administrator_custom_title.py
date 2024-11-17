from aiogram.methods import SetChatAdministratorCustomTitle
from tests.mocked_bot import MockedBot


class TestSetChatTitle:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatAdministratorCustomTitle, ok=True, result=True)

        response: bool = await bot.set_chat_administrator_custom_title(
            chat_id=-42, user_id=42, custom_title="test chat"
        )
        request = bot.get_request()
        assert response == prepare_result.result
