import pytest
from aiogram.api.methods import GetStickerSet, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetStickerSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetStickerSet, ok=True, result=None)

        response: StickerSet = await GetStickerSet(name=...,)
        request: Request = bot.get_request()
        assert request.method == "getStickerSet"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetStickerSet, ok=True, result=None)

        response: StickerSet = await bot.get_sticker_set(name=...,)
        request: Request = bot.get_request()
        assert request.method == "getStickerSet"
        # assert request.data == {}
        assert response == prepare_result.result
