from aiogram.methods import UnbanChatSenderChat
from tests.mocked_bot import MockedBot


class TestUnbanChatSenderChat:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnbanChatSenderChat, ok=True, result=True)

        response: bool = await bot.unban_chat_sender_chat(
            chat_id=-42,
            sender_chat_id=-1337,
        )
        bot.get_request()
        assert response == prepare_result.result
