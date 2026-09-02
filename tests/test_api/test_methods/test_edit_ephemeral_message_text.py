from aiogram.methods import EditEphemeralMessageText
from tests.mocked_bot import MockedBot


class TestEditEphemeralMessageText:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditEphemeralMessageText, ok=True, result=True)

        response: bool = await bot.edit_ephemeral_message_text(
            chat_id=42, receiver_user_id=42, ephemeral_message_id=42, text="text"
        )
        bot.get_request()
        assert response == prepare_result.result
