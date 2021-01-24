import pytest

from aiogram.methods import Request, UnpinAllChatMessages
from tests.mocked_bot import MockedBot


class TestUnpinAllChatMessages:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinAllChatMessages, ok=True, result=True)

        response: bool = await UnpinAllChatMessages(
            chat_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "unpinAllChatMessages"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinAllChatMessages, ok=True, result=True)

        response: bool = await bot.unpin_all_chat_messages(
            chat_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "unpinAllChatMessages"
        # assert request.data == {}
        assert response == prepare_result.result
