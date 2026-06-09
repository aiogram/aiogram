from aiogram.methods import SetChatTitle
from tests.mocked_bot import MockedBot


class TestSetChatTitle:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatTitle, ok=True, result=True)

        response: bool = await bot.set_chat_title(chat_id=-42, title="test chat")
        bot.get_request()
        assert response == prepare_result.result
