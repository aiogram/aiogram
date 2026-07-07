import datetime

from aiogram.methods import SendMediaGroup
from aiogram.types import (
    BufferedInputFile,
    Chat,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    PhotoSize,
    Video,
)
from tests.mocked_bot import MockedBot


class TestSendMediaGroup:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendMediaGroup,
            ok=True,
            result=[
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    photo=[
                        PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                    ],
                    media_group_id="media group",
                    chat=Chat(id=42, type="private"),
                ),
                Message(
                    message_id=43,
                    date=datetime.datetime.now(),
                    video=Video(
                        file_id="file id",
                        width=42,
                        height=42,
                        duration=0,
                        file_unique_id="file id",
                    ),
                    media_group_id="media group",
                    chat=Chat(id=42, type="private"),
                ),
            ],
        )

        response: list[Message] = await bot.send_media_group(
            chat_id=42,
            media=[
                InputMediaPhoto(media="file id"),
                InputMediaVideo(media=BufferedInputFile(b"", "video.mp4")),
            ],
        )
        bot.get_request()
        assert response == prepare_result.result
