import pytest

from aiogram.api.methods import DeleteChatStickerSet, Request
from tests.mocked_bot import MockedBot


class TestDeleteChatStickerSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteChatStickerSet, ok=True, result=True)

        response: bool = await DeleteChatStickerSet(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "deleteChatStickerSet"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteChatStickerSet, ok=True, result=True)

        response: bool = await bot.delete_chat_sticker_set(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "deleteChatStickerSet"
        assert response == prepare_result.result
