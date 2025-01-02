from aiogram.methods import VerifyChat
from aiogram.types import Poll
from tests.mocked_bot import MockedBot


class TestVerifyChat:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(VerifyChat, ok=True, result=True)

        response: bool = await bot.verify_chat(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
