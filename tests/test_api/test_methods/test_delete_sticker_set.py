from aiogram.methods import DeleteStickerSet, Request
from tests.mocked_bot import MockedBot


class TestDeleteStickerSet:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerSet, ok=True, result=True)

        response: bool = await DeleteStickerSet(name="test")
        request: Request = bot.get_request()
        assert request.method == "deleteStickerSet"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerSet, ok=True, result=True)

        response: bool = await bot.delete_sticker_set(name="test")
        request: Request = bot.get_request()
        assert request.method == "deleteStickerSet"
        assert response == prepare_result.result
