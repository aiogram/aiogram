import pytest

from aiogram.api.methods import DeleteChatPhoto, Request
from tests.mocked_bot import MockedBot


class TestDeleteChatPhoto:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteChatPhoto, ok=True, result=True)

        response: bool = await DeleteChatPhoto(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "deleteChatPhoto"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteChatPhoto, ok=True, result=True)

        response: bool = await bot.delete_chat_photo(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "deleteChatPhoto"
        assert response == prepare_result.result
