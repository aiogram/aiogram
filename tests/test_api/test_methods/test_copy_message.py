import pytest

from aiogram.methods import CopyMessage, Request
from aiogram.types import MessageId
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestCopyMessage:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CopyMessage, ok=True, result=MessageId(message_id=42))

        response: MessageId = await CopyMessage(
            chat_id=42,
            from_chat_id=42,
            message_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "copyMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CopyMessage, ok=True, result=MessageId(message_id=42))

        response: MessageId = await bot.copy_message(
            chat_id=42,
            from_chat_id=42,
            message_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "copyMessage"
        # assert request.data == {}
        assert response == prepare_result.result
