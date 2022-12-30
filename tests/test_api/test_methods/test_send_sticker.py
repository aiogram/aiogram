import datetime

from aiogram.methods import Request, SendSticker
from aiogram.types import Chat, Message, Sticker
from tests.mocked_bot import MockedBot


class TestSendSticker:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendSticker,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                sticker=Sticker(
                    file_id="file id",
                    width=42,
                    height=42,
                    is_animated=False,
                    is_video=False,
                    file_unique_id="file id",
                    type="regular",
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendSticker(chat_id=42, sticker="file id")
        request: Request = bot.get_request()
        assert request.method == "sendSticker"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendSticker,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                sticker=Sticker(
                    file_id="file id",
                    width=42,
                    height=42,
                    is_animated=False,
                    is_video=False,
                    file_unique_id="file id",
                    type="regular",
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_sticker(chat_id=42, sticker="file id")
        request: Request = bot.get_request()
        assert request.method == "sendSticker"
        assert response == prepare_result.result
