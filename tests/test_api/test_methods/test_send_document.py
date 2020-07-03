import datetime

import pytest

from aiogram.api.methods import Request, SendDocument
from aiogram.api.types import Chat, Document, Message
from tests.mocked_bot import MockedBot


class TestSendDocument:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendDocument,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                document=Document(file_id="file id", file_unique_id="file id"),
                chat=private_chat,
            ),
        )

        response: Message = await SendDocument(chat_id=private_chat.id, document="file id")
        request: Request = bot.get_request()
        assert request.method == "sendDocument"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendDocument,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                document=Document(file_id="file id", file_unique_id="file id"),
                chat=private_chat,
            ),
        )

        response: Message = await bot.send_document(chat_id=private_chat.id, document="file id")
        request: Request = bot.get_request()
        assert request.method == "sendDocument"
        assert response == prepare_result.result
