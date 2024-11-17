import datetime

from aiogram.methods import SendPhoto
from aiogram.types import Chat, Message, PhotoSize
from tests.mocked_bot import MockedBot


class TestSendPhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendPhoto,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                photo=[
                    PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                ],
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_photo(chat_id=42, photo="file id")
        request = bot.get_request()
        assert response == prepare_result.result
