from aiogram.methods import DeleteBusinessMessages
from tests.mocked_bot import MockedBot


class TestDeleteBusinessMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteBusinessMessages, ok=True, result=True)

        response: bool = await bot.delete_business_messages(
            business_connection_id="test_connection_id", message_ids=[1, 2, 3]
        )
        bot.get_request()
        assert response == prepare_result.result
