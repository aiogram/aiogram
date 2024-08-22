from aiogram.methods import PinChatMessage
from tests.mocked_bot import MockedBot


class TestPinChatMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PinChatMessage, ok=True, result=True)

        response: bool = await bot.pin_chat_message(chat_id=-42, message_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
