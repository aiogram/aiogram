from aiogram.methods import DeleteEphemeralMessage
from tests.mocked_bot import MockedBot


class TestDeleteEphemeralMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteEphemeralMessage, ok=True, result=True)

        response: bool = await bot.delete_ephemeral_message(
            chat_id=42, receiver_user_id=42, ephemeral_message_id=42
        )
        bot.get_request()
        assert response == prepare_result.result
