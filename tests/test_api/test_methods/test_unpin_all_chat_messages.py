from aiogram.methods import UnpinAllChatMessages
from tests.mocked_bot import MockedBot


class TestUnpinAllChatMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinAllChatMessages, ok=True, result=True)

        response: bool = await bot.unpin_all_chat_messages(
            chat_id=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
