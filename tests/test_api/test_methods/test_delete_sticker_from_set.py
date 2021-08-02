import pytest

from aiogram.methods import DeleteStickerFromSet, Request
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestDeleteStickerFromSet:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerFromSet, ok=True, result=True)

        response: bool = await DeleteStickerFromSet(sticker="sticker id")
        request: Request = bot.get_request()
        assert request.method == "deleteStickerFromSet"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerFromSet, ok=True, result=True)

        response: bool = await bot.delete_sticker_from_set(sticker="sticker id")
        request: Request = bot.get_request()
        assert request.method == "deleteStickerFromSet"
        assert response == prepare_result.result
