from aiogram.methods import DeleteMessage
from tests.mocked_bot import MockedBot


class TestDeleteMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteMessage, ok=True, result=True)

        response: bool = await bot.delete_message(chat_id=42, message_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
