import datetime

import pytest

from aiogram.api.methods import Request, SendDocument
from aiogram.api.types import Chat, Document, Message
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendDocument:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendDocument,
            ok=True,
            result=MessageFactory(
                document=Document(file_id="file id", file_unique_id="file id"),
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
            result=MessageFactory(
                document=Document(file_id="file id", file_unique_id="file id"),
            ),
        )

        response: Message = await bot.send_document(chat_id=private_chat.id, document="file id")
        request: Request = bot.get_request()
        assert request.method == "sendDocument"
        assert response == prepare_result.result
