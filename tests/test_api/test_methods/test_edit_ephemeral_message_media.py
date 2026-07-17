from aiogram.methods import EditEphemeralMessageMedia
from aiogram.types import BufferedInputFile, InputMediaPhoto
from tests.mocked_bot import MockedBot


class TestEditEphemeralMessageMedia:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditEphemeralMessageMedia, ok=True, result=True)

        response: bool = await bot.edit_ephemeral_message_media(
            chat_id=42,
            receiver_user_id=42,
            ephemeral_message_id=42,
            media=InputMediaPhoto(media=BufferedInputFile(b"", "photo.png")),
        )
        bot.get_request()
        assert response == prepare_result.result
