from aiogram.methods import Request, UnbanChatSenderChat
from tests.mocked_bot import MockedBot


class TestUnbanChatSenderChat:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatSenderChat, ok=True, result=True)

        response: bool = await UnbanChatSenderChat(
            chat_id=-42,
            sender_chat_id=-1337,
        )
        request: Request = bot.get_request()
        assert request.method == "unbanChatSenderChat"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatSenderChat, ok=True, result=True)

        response: bool = await bot.unban_chat_sender_chat(
            chat_id=-42,
            sender_chat_id=-1337,
        )
        request: Request = bot.get_request()
        assert request.method == "unbanChatSenderChat"
        # assert request.data == {}
        assert response == prepare_result.result
