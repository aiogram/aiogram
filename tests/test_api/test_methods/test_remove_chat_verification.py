from aiogram.methods import RemoveChatVerification
from tests.mocked_bot import MockedBot


class TestRemoveChatVerification:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RemoveChatVerification, ok=True, result=True)

        response: bool = await bot.remove_chat_verification(chat_id=42)
        bot.get_request()
        assert response == prepare_result.result
