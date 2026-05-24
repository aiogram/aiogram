import datetime

from aiogram.methods import SendLivePhoto
from aiogram.types import Chat, LivePhoto, Message, User
from tests.mocked_bot import MockedBot


class TestSendLivePhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendLivePhoto,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                live_photo=LivePhoto(
                    file_id="file_id",
                    file_unique_id="file_unique_id",
                    width=640,
                    height=480,
                    duration=3,
                ),
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
            ),
        )

        response: Message = await bot.send_live_photo(
            chat_id=42,
            live_photo="file_id",
            photo="photo_file_id",
        )
        bot.get_request()
        assert response == prepare_result.result
