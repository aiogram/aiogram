import datetime

from aiogram.methods import Request, SendVideoNote
from aiogram.types import BufferedInputFile, Chat, Message, VideoNote
from tests.mocked_bot import MockedBot


class TestSendVideoNote:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVideoNote,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                video_note=VideoNote(
                    file_id="file id", length=0, duration=0, file_unique_id="file id"
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendVideoNote(
            chat_id=42,
            video_note="file id",
            thumbnail=BufferedInputFile(b"", "file.png"),
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideoNote"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVideoNote,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                video_note=VideoNote(
                    file_id="file id", length=0, duration=0, file_unique_id="file id"
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_video_note(
            chat_id=42,
            video_note="file id",
            thumbnail=BufferedInputFile(b"", "file.png"),
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideoNote"
        assert response == prepare_result.result
