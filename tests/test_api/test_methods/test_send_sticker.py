import datetime

import pytest

from aiogram.api.methods import Request, SendSticker
from aiogram.api.types import Chat, Message, Sticker
from tests.mocked_bot import MockedBot


class TestSendSticker:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
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
                    file_unique_id="file id",
                ),
                chat=private_chat,
            ),
        )

        response: Message = await SendSticker(chat_id=private_chat.id, sticker="file id")
        request: Request = bot.get_request()
        assert request.method == "sendSticker"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
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
                    file_unique_id="file id",
                ),
                chat=private_chat,
            ),
        )

        response: Message = await bot.send_sticker(chat_id=private_chat.id, sticker="file id")
        request: Request = bot.get_request()
        assert request.method == "sendSticker"
        assert response == prepare_result.result
