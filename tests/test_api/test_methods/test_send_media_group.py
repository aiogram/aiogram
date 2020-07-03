import datetime
from typing import List

import pytest

from aiogram.api.methods import Request, SendMediaGroup
from aiogram.api.types import (
    BufferedInputFile,
    Chat,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    PhotoSize,
    Video,
)
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendMediaGroup:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendMediaGroup,
            ok=True,
            result=[
                MessageFactory(
                    photo=[
                        PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                    ],
                    media_group_id="media group",
                ),
                MessageFactory(
                    video=Video(
                        file_id="file id",
                        width=42,
                        height=42,
                        duration=0,
                        file_unique_id="file id",
                    ),
                    media_group_id="media group",
                ),
            ],
        )

        response: List[Message] = await SendMediaGroup(
            chat_id=private_chat.id,
            media=[
                InputMediaPhoto(media="file id"),
                InputMediaVideo(media=BufferedInputFile(b"", "video.mp4")),
            ],
        )
        request: Request = bot.get_request()
        assert request.method == "sendMediaGroup"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendMediaGroup,
            ok=True,
            result=[
                MessageFactory(
                    photo=[
                        PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                    ],
                    media_group_id="media group",
                ),
                MessageFactory(
                    video=Video(
                        file_id="file id",
                        width=42,
                        height=42,
                        duration=0,
                        file_unique_id="file id",
                    ),
                    media_group_id="media group",
                ),
            ],
        )

        response: List[Message] = await bot.send_media_group(
            chat_id=private_chat.id,
            media=[
                InputMediaPhoto(media="file id"),
                InputMediaVideo(media=BufferedInputFile(b"", "video.mp4")),
            ],
        )
        request: Request = bot.get_request()
        assert request.method == "sendMediaGroup"
        assert response == prepare_result.result
