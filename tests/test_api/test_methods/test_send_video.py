import datetime

from aiogram.methods import SendVideo
from aiogram.types import Chat, Message, Video
from tests.mocked_bot import MockedBot


class TestSendVideo:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVideo,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                video=Video(
                    file_id="file id", width=42, height=42, duration=0, file_unique_id="file id"
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_video(chat_id=42, video="file id")
        request = bot.get_request()
        assert response == prepare_result.result
