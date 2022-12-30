from aiogram.methods import Request, UnpinChatMessage
from tests.mocked_bot import MockedBot


class TestUnpinChatMessage:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinChatMessage, ok=True, result=True)

        response: bool = await UnpinChatMessage(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "unpinChatMessage"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinChatMessage, ok=True, result=True)

        response: bool = await bot.unpin_chat_message(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "unpinChatMessage"
        assert response == prepare_result.result
