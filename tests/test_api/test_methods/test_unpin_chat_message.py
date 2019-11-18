import pytest
from aiogram.api.methods import Request, UnpinChatMessage
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestUnpinChatMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinChatMessage, ok=True, result=None)

        response: bool = await UnpinChatMessage(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "unpinChatMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinChatMessage, ok=True, result=None)

        response: bool = await bot.unpin_chat_message(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "unpinChatMessage"
        # assert request.data == {}
        assert response == prepare_result.result
