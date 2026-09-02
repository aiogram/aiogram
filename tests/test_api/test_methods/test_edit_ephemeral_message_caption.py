from aiogram.methods import EditEphemeralMessageCaption
from tests.mocked_bot import MockedBot


class TestEditEphemeralMessageCaption:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditEphemeralMessageCaption, ok=True, result=True)

        response: bool = await bot.edit_ephemeral_message_caption(
            chat_id=42, receiver_user_id=42, ephemeral_message_id=42
        )
        bot.get_request()
        assert response == prepare_result.result
