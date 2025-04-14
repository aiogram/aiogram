from aiogram.methods import ReadBusinessMessage
from tests.mocked_bot import MockedBot


class TestReadBusinessMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ReadBusinessMessage, ok=True, result=True)

        response: bool = await bot.read_business_message(
            business_connection_id="test_connection_id", chat_id=123456789, message_id=42
        )
        request = bot.get_request()
        assert response == prepare_result.result
