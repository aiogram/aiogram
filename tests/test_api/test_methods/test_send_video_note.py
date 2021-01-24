import datetime

import pytest

from aiogram.api.methods import Request, SendVideoNote
from aiogram.api.types import BufferedInputFile, Chat, Message, VideoNote
from tests.mocked_bot import MockedBot


class TestSendVideoNote:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendVideoNote,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                video_note=VideoNote(
                    file_id="file id", length=0, duration=0, file_unique_id="file id"
                ),
                chat=private_chat,
            ),
        )

        response: Message = await SendVideoNote(
            chat_id=private_chat.id, video_note="file id", thumb=BufferedInputFile(b"", "file.png")
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideoNote"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendVideoNote,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                video_note=VideoNote(
                    file_id="file id", length=0, duration=0, file_unique_id="file id"
                ),
                chat=private_chat,
            ),
        )

        response: Message = await bot.send_video_note(
            chat_id=private_chat.id, video_note="file id", thumb=BufferedInputFile(b"", "file.png")
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideoNote"
        assert response == prepare_result.result
