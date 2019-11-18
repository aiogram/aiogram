import pytest
from aiogram.api.methods import DeleteStickerFromSet, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestDeleteStickerFromSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerFromSet, ok=True, result=None)

        response: bool = await DeleteStickerFromSet(sticker=...,)
        request: Request = bot.get_request()
        assert request.method == "deleteStickerFromSet"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerFromSet, ok=True, result=None)

        response: bool = await bot.delete_sticker_from_set(sticker=...,)
        request: Request = bot.get_request()
        assert request.method == "deleteStickerFromSet"
        # assert request.data == {}
        assert response == prepare_result.result
