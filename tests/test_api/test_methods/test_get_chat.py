from aiogram.methods import GetChat, Request
from aiogram.types import Chat
from tests.mocked_bot import MockedBot


class TestGetChat:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChat, ok=True, result=Chat(id=-42, type="channel", title="chat")
        )

        response: Chat = await bot.get_chat(chat_id=-42)
        request = bot.get_request()
        assert response == prepare_result.result
