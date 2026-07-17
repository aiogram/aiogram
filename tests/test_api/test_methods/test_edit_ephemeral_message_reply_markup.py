from aiogram.methods import EditEphemeralMessageReplyMarkup
from tests.mocked_bot import MockedBot


class TestEditEphemeralMessageReplyMarkup:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditEphemeralMessageReplyMarkup, ok=True, result=True)

        response: bool = await bot.edit_ephemeral_message_reply_markup(
            chat_id=42, receiver_user_id=42, ephemeral_message_id=42
        )
        bot.get_request()
        assert response == prepare_result.result
