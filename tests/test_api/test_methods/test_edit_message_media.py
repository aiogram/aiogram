from typing import Union

from aiogram.methods import EditMessageMedia
from aiogram.types import BufferedInputFile, InputMediaPhoto, Message
from tests.mocked_bot import MockedBot


class TestEditMessageMedia:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageMedia, ok=True, result=True)

        response: Union[Message, bool] = await bot.edit_message_media(
            media=InputMediaPhoto(media=BufferedInputFile(b"", "photo.png"))
        )
        request = bot.get_request()
        assert response == prepare_result.result
