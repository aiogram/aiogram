from aiogram.methods import Request, SetChatDescription
from tests.mocked_bot import MockedBot


class TestSetChatDescription:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatDescription, ok=True, result=True)

        response: bool = await bot.set_chat_description(chat_id=-42, description="awesome chat")
        request = bot.get_request()
        assert response == prepare_result.result
