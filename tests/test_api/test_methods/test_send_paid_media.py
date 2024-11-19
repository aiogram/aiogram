import datetime

from aiogram.methods import SendPaidMedia
from aiogram.types import (
    Chat,
    InputPaidMediaPhoto,
    Message,
    PaidMediaInfo,
    PaidMediaPhoto,
    PhotoSize,
)
from tests.mocked_bot import MockedBot


class TestSendPaidMedia:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendPaidMedia,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                chat=Chat(id=42, type="private"),
                paid_media=PaidMediaInfo(
                    paid_media=[
                        PaidMediaPhoto(
                            photo=[
                                PhotoSize(
                                    file_id="test", width=42, height=42, file_unique_id="test"
                                )
                            ]
                        )
                    ],
                    star_count=1,
                ),
            ),
        )

        response: Message = await bot.send_paid_media(
            chat_id=-42, star_count=1, media=[InputPaidMediaPhoto(media="file_id")]
        )
        request = bot.get_request()
        assert response == prepare_result.result
