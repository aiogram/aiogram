from aiogram.methods import DeleteMessages
from tests.mocked_bot import MockedBot


class TestDeleteMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            DeleteMessages,
            ok=True,
            result=True,
        )

        response: bool = await bot.delete_messages(
            chat_id=42,
            message_ids=[13, 77],
        )
        request = bot.get_request()
        assert request
        assert response == prepare_result.result
